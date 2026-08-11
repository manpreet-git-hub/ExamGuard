# ── utils/logger.py — CSV violation logging system ────────────────────────────

import csv
from datetime import datetime

import streamlit as st


def log_event(event: str, penalty: int = 0):
    """
    Append a violation to the rolling in-memory log and write a CSV row.

    Args:
        event:   Human-readable description of the violation.
        penalty: Points deducted (0 if informational only).
    """
    ts  = datetime.now().strftime("%H:%M:%S")
    lvl = (
        "red"
        if any(w in event for w in ["Phone", "Multiple", "ALERT", "No Face"])
        else "yellow"
    )
    entry = {
        "text":        event,
        "time":        ts,
        "level":       lvl,
        "penalty":     penalty,
        "score_after": st.session_state.integrity_score,
    }
    st.session_state.violations.appendleft(entry)
    st.session_state.total_viol += 1

    try:
        with open("proctor_log.csv", "a", newline="") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(),
                event,
                f"-{penalty}" if penalty else "0",
                st.session_state.integrity_score,
            ])
    except Exception:
        pass


def log_evidence_row(record: dict):
    """
    Write an evidence-capture event to the CSV log.

    Args:
        record: Evidence record dict containing ts_iso, label, score, filename.
    """
    try:
        with open("proctor_log.csv", "a", newline="") as f:
            csv.writer(f).writerow([
                record["ts_iso"],
                f"EVIDENCE_CAPTURE — {record['label']}",
                "0",
                record["score"],
                record["filename"],
            ])
    except Exception:
        pass
