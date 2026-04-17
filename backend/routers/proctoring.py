# ── backend/routers/proctoring.py — Violation logging + evidence ──────────────

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os, base64, uuid

from database.db import get_db
from models.models import ViolationLog, Submission, User
from routers.auth import get_current_user

router = APIRouter()

EVIDENCE_DIR = "storage/evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

PENALTIES = {
    "phone_detected":    30,
    "multiple_faces":    50,
    "no_face":           15,
    "tab_switched":      15,
    "looking_away":       5,
    "eye_gaze_away":      5,
    "talking":            8,
    "fullscreen_exit":   10,
    "copy_paste":         5,
    "network_disconnect": 5,
    "laptop_detected":   25,
}

def compute_risk_level(integrity_score: float) -> str:
    if integrity_score >= 80:
        return "Low"
    elif integrity_score >= 50:
        return "Medium"
    return "High"


class ViolationCreate(BaseModel):
    submission_id: int
    violation_type: str
    confidence_score: float = 1.0
    description: Optional[str] = None
    evidence_b64: Optional[str] = None   # base64 encoded image


class ViolationOut(BaseModel):
    id: int
    submission_id: int
    student_id: int
    test_id: int
    violation_type: str
    confidence_score: float
    description: Optional[str]
    evidence_path: Optional[str]
    timestamp: datetime
    penalty_applied: int

    class Config:
        from_attributes = True


@router.post("/violation", response_model=ViolationOut, status_code=201)
def log_violation(
    data: ViolationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Submission).filter(
        Submission.id == data.submission_id,
        Submission.student_id == current_user.id,
        Submission.is_submitted == False
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Active submission not found")

    # Save evidence image
    evidence_path = None
    if data.evidence_b64:
        try:
            img_data = base64.b64decode(data.evidence_b64)
            fname = f"{data.violation_type}_{datetime.utcnow().strftime('%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
            fpath = os.path.join(EVIDENCE_DIR, fname)
            with open(fpath, "wb") as f:
                f.write(img_data)
            evidence_path = f"/evidence/{fname}"
        except Exception as e:
            pass  # Non-critical

    penalty = PENALTIES.get(data.violation_type, 0)

    log = ViolationLog(
        submission_id=data.submission_id,
        student_id=current_user.id,
        test_id=sub.test_id,
        violation_type=data.violation_type,
        confidence_score=data.confidence_score,
        description=data.description,
        evidence_path=evidence_path,
        penalty_applied=penalty,
    )
    db.add(log)

    # Update integrity score
    new_score = max(0, sub.integrity_score - penalty)
    sub.integrity_score = new_score
    sub.risk_level = compute_risk_level(new_score)

    db.commit()
    db.refresh(log)
    return log


@router.get("/violations/{submission_id}", response_model=List[ViolationOut])
def get_violations(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    return sub.violations


@router.get("/integrity/{submission_id}")
def get_integrity_score(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "integrity_score": sub.integrity_score,
        "risk_level": sub.risk_level,
        "violations_count": len(sub.violations),
    }
