# ── utils/evidence.py — Screenshot evidence capture system ────────────────────

import os
import time
from datetime import datetime

import cv2
import streamlit as st

from config import SCREENSHOT_COOLDOWN, EVIDENCE_DIR, VTYPE_META
from utils.logger import log_evidence_row


def capture_evidence(frame, violation_type: str) -> str | None:
    """
    Save a timestamped, watermarked screenshot for a given violation type.
    Enforces a per-type cooldown of SCREENSHOT_COOLDOWN seconds to prevent spam.

    Args:
        frame:          BGR numpy array — the raw (un-annotated) camera frame.
        violation_type: Key from VTYPE_META (e.g. "phone", "no_face").

    Returns:
        str | None: Saved filepath on success, or None if skipped/failed.
    """
    now  = time.time()
    last = st.session_state.screenshot_cooldowns.get(violation_type, 0)
    if now - last < SCREENSHOT_COOLDOWN:
        return None   # still within cooldown window

    # Build filename: sessionID_violationType_YYYY-MM-DD_HH-MM-SS.jpg
    ts_str   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sid      = st.session_state.session_id
    vslug    = violation_type.replace(" ", "_")
    filename = f"{sid}_{vslug}_{ts_str}.jpg"
    filepath = os.path.join(EVIDENCE_DIR, filename)

    # Stamp frame with a semi-transparent banner before saving
    stamped = frame.copy()
    fh, fw  = stamped.shape[:2]
    label, banner_color = VTYPE_META.get(
        violation_type, (violation_type.upper(), (0, 51, 255))
    )

    overlay = stamped.copy()
    cv2.rectangle(overlay, (0, fh - 44), (fw, fh), banner_color, -1)
    cv2.addWeighted(overlay, 0.55, stamped, 0.45, 0, stamped)

    cv2.putText(
        stamped, f"EVIDENCE: {label}", (10, fh - 26),
        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA,
    )
    cv2.putText(
        stamped,
        f"{sid}  {datetime.now().strftime('%H:%M:%S')}",
        (10, fh - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 220, 230), 1, cv2.LINE_AA,
    )

    success = cv2.imwrite(filepath, stamped)
    if not success:
        return None

    # Update cooldown tracker
    st.session_state.screenshot_cooldowns[violation_type] = now

    # Build and store evidence record
    record = {
        "path":    filepath,
        "filename": filename,
        "vtype":   violation_type,
        "label":   label,
        "ts":      datetime.now().strftime("%H:%M:%S"),
        "ts_iso":  datetime.now().isoformat(),
        "score":   st.session_state.integrity_score,
    }
    st.session_state.evidence_log.append(record)
    log_evidence_row(record)

    return filepath
