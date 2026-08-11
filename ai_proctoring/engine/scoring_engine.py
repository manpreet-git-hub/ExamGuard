# ── engine/scoring_engine.py — Integrity score + violation timers ─────────────

import time
from datetime import datetime

import streamlit as st

from config import (
    PENALTIES, PERSIST_THRESHOLD, REARM_COOLDOWN, MIN_SCORE,
    EYE_GAZE_AWAY_DIRECTIONS,
)
from utils.logger import log_event


def severity_label(score):
    """Return (label, badge_css_class, hex_color) for a given integrity score."""
    if score >= 80:
        return "Normal",     "badge-green",  "#00ff88"
    if score >= 60:
        return "Warning",    "badge-yellow", "#ffcc00"
    if score >= 40:
        return "Suspicious", "badge-yellow", "#ffcc00"
    return "High Risk", "badge-red", "#ff3355"


def risk_classification(score):
    """Map integrity score to a risk class string."""
    if score >= 80:
        return "Safe"
    if score >= 50:
        return "Suspicious"
    return "Cheating"


def update_integrity_score(det: dict):
    """
    Evaluate detections against per-violation persist-timers and deduct
    integrity points when a violation exceeds PERSIST_THRESHOLD seconds.

    Args:
        det: results dict returned by process_frame().

    Returns:
        set: violation-type keys that are currently active (confirmed).
    """
    now    = time.time()
    timers = st.session_state.violation_timers
    active = set()

    # Eye gaze is treated as a separate violation from head-pose "looking_away"
    eye_gaze_away = det.get("eye") in EYE_GAZE_AWAY_DIRECTIONS

    checks = {
        "multi_face":    det["num_faces"] > 1,
        "no_face":       det["num_faces"] == 0,
        "phone":         det["phone"],
        "laptop":        det.get("laptop", False),
        "looking_away":  det["head_state"] in ("warn", "alert"),
        "eye_gaze_away": eye_gaze_away,
        "talking":       det["talking"],
    }

    label_map = {
        "multi_face":    "Multiple faces detected",
        "no_face":       "No face detected",
        "phone":         "Phone detected",
        "laptop":        "Laptop detected",
        "looking_away":  f"Looking away ({det['head']})",
        "eye_gaze_away": f"Eye gaze: {det.get('eye', 'Unknown')}",
        "talking":       "Talking detected",
    }

    for vtype, triggered in checks.items():
        if triggered:
            if vtype not in timers:
                timers[vtype] = now       # start persistence clock
            elapsed = now - timers[vtype]

            if elapsed >= PERSIST_THRESHOLD:
                active.add(vtype)
                cooldown_key = f"_last_penalty_{vtype}"
                last_penalty = timers.get(cooldown_key, 0)

                if now - last_penalty >= REARM_COOLDOWN:
                    penalty = PENALTIES.get(vtype, 0)
                    st.session_state.integrity_score = max(
                        MIN_SCORE,
                        st.session_state.integrity_score - penalty,
                    )
                    timers[cooldown_key] = now

                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "violation": label_map[vtype],
                        "penalty":   penalty,
                        "score":     st.session_state.integrity_score,
                    }
                    st.session_state.score_log.append(log_entry)
                    log_event(label_map[vtype], penalty)

                # ── Trigger video clip evidence (replaces screenshot) ─────
                if "current_frame" in st.session_state:
                    from utils.video_recorder import start_recording
                    start_recording(vtype)

        else:
            timers.pop(vtype, None)

    st.session_state.violation_timers  = timers
    st.session_state.active_violations = active
    return active


def generate_final_report():
    """Build and return a summary report dict for the current session."""
    score    = st.session_state.integrity_score
    log      = st.session_state.score_log
    duration = 0
    if st.session_state.session_start:
        duration = int(time.time() - st.session_state.session_start)

    tally = {}
    for entry in log:
        vtype = entry["violation"]
        tally.setdefault(vtype, {"count": 0, "total_penalty": 0})
        tally[vtype]["count"]         += 1
        tally[vtype]["total_penalty"] += entry["penalty"]

    report = {
        "session_id":        st.session_state.session_id,
        "final_score":       score,
        "risk_class":        risk_classification(score),
        "severity":          severity_label(score)[0],
        "duration_seconds":  duration,
        "total_violations":  len(log),
        "violation_summary": tally,
        "violation_log":     log,
    }
    st.session_state.final_report = report
    return report
