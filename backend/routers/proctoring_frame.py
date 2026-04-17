# ── backend/routers/proctoring_frame.py — AI frame analysis endpoint ──────────
# This module adds the /api/proctoring/analyze-frame endpoint that receives
# base64-encoded frames from students and runs the full AI proctoring pipeline.
# It requires the ai_proctoring module to be in PYTHONPATH.

import os, sys, base64, traceback
import numpy as np
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
AI_ROOT = os.path.join(PROJECT_ROOT, 'ai_proctoring')
for path in [PROJECT_ROOT, AI_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from database.db import get_db
from models.models import Submission, ViolationLog
from routers.auth import get_current_user
from models.models import User

router_frame = APIRouter()
AI_VIOLATION_COOLDOWN_SECONDS = 8

# Lazy-load AI models (heavy — only on first request)
_models = None

def get_models():
    global _models
    if _models is not None:
        return _models
    try:
        from ai_proctoring.model_loader import load_models
        _models = load_models()
        print("[Proctoring] AI models loaded successfully")
    except Exception as e:
        print(f"[Proctoring] AI model load failed: {e}")
        _models = {}
    return _models


PENALTIES = {
    "phone_detected": 30,
    "multiple_faces": 50,
    "no_face":      15,
    "looking_away": 5,
    "eye_gaze_away": 5,
    "talking":      8,
    "laptop_detected": 25,
}


class FrameAnalysisRequest(BaseModel):
    submission_id: int
    frame_b64: str


def _normalize_dt(value):
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(tzinfo=None) if getattr(value, "tzinfo", None) else value


def _recent_duplicate_exists(db: Session, submission_id: int, violation_type: str) -> bool:
    last_log = (
        db.query(ViolationLog)
        .filter(
            ViolationLog.submission_id == submission_id,
            ViolationLog.violation_type == violation_type,
        )
        .order_by(ViolationLog.timestamp.desc())
        .first()
    )
    if not last_log or not last_log.timestamp:
        return False

    last_seen = _normalize_dt(last_log.timestamp)
    if last_seen is None:
        return False

    age = (datetime.utcnow() - last_seen).total_seconds()
    return age < AI_VIOLATION_COOLDOWN_SECONDS


@router_frame.post("/analyze-frame")
async def analyze_frame(
    req: FrameAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Receive a JPEG frame (base64), run full AI proctoring pipeline,
    and log any violations to the database.
    """
    # Validate submission
    sub = db.query(Submission).filter(
        Submission.id == req.submission_id,
        Submission.student_id == current_user.id,
        Submission.is_submitted == False
    ).first()
    if not sub:
        return {"ok": False, "reason": "no active submission"}

    try:
        import cv2
        # Decode frame
        img_data = base64.b64decode(req.frame_b64)
        arr      = np.frombuffer(img_data, dtype=np.uint8)
        frame    = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return {"ok": False, "reason": "invalid frame"}

        models = get_models()
        if not models:
            return {"ok": True, "violations": [], "note": "AI models unavailable"}

        # Run proctoring pipeline
        from ai_proctoring.engine.frame_processor import process_frame
        _, results = process_frame(frame, models)

        violations_logged = []

        # Map results to violations
        checks = {
            "phone_detected": (results.get("phone"),                                "Phone detected on camera"),
            "laptop_detected": (results.get("laptop"),                              "Laptop detected on camera"),
            "multiple_faces": (results.get("num_faces", 0) > 1,                   "Multiple faces detected"),
            "no_face":        (results.get("num_faces", 0) == 0,                  "No face detected"),
            "looking_away":   (results.get("head_state") in ("warn", "alert"),    f"Head pose: {results.get('head', '')}"),
            "eye_gaze_away":  (results.get("eye_state") == "warn",                 f"Eye status: {results.get('eye','')}"),
            "talking":        (results.get("talking"),                             "Talking detected"),
        }

        for vtype, (triggered, desc) in checks.items():
            if triggered:
                if _recent_duplicate_exists(db, sub.id, vtype):
                    continue
                penalty = PENALTIES.get(vtype, 0)
                log = ViolationLog(
                    submission_id=sub.id,
                    student_id=current_user.id,
                    test_id=sub.test_id,
                    violation_type=vtype,
                    confidence_score=results.get("suspicion", 50) / 100,
                    description=desc,
                    penalty_applied=penalty,
                )
                db.add(log)
                sub.integrity_score = max(0, sub.integrity_score - penalty)
                db.flush()
                violations_logged.append({
                    "id": log.id,
                    "violation_type": vtype,
                    "description": desc,
                    "confidence_score": results.get("suspicion", 50) / 100,
                    "penalty_applied": penalty,
                    "timestamp": datetime.utcnow().isoformat(),
                    "student_id": current_user.id,
                    "test_id": sub.test_id,
                })

        if violations_logged:
            # Compute risk
            s = sub.integrity_score
            sub.risk_level = "Low" if s >= 80 else "Medium" if s >= 50 else "High"
            db.commit()

        return {
            "ok":         True,
            "events":     violations_logged,
            "violations": [item["violation_type"] for item in violations_logged],
            "num_faces":  results.get("num_faces", 0),
            "suspicion":  results.get("suspicion", 0),
            "integrity":  sub.integrity_score,
            "risk_level": sub.risk_level,
            "checks_available": {
                "face": "face_det" in models,
                "mesh": "face_mesh" in models,
                "yolo": "yolo" in models,
            },
        }

    except Exception as e:
        traceback.print_exc()
        return {"ok": False, "error": str(e)}
