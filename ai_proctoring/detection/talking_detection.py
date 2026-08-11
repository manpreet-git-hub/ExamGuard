# ── detection/talking_detection.py — Mouth-movement / talking detection ────────

from runtime_state import get_state, set_state


def detect_talking(face):
    """
    Detect whether the subject is talking by measuring lip-gap movement.

    Uses two Streamlit session-state counters:
        st.session_state.prev_mouth_dist   – last frame's lip-gap distance
        st.session_state.talking_counter   – rolling confidence counter (0–20)

    Args:
        face: list of [x, y] pixel coordinates for all FaceMesh landmarks.

    Returns:
        bool: True if talking is detected.
    """
    upper = face[13]
    lower = face[14]
    dist  = abs(upper[1] - lower[1])

    prev_mouth_dist = get_state("prev_mouth_dist", 0)
    talking_counter = get_state("talking_counter", 0)

    movement = abs(dist - prev_mouth_dist)
    set_state("prev_mouth_dist", dist)

    if movement > 3:
        talking_counter = min(talking_counter + 1, 20)
    else:
        talking_counter = max(0, talking_counter - 1)

    set_state("talking_counter", talking_counter)
    return talking_counter > 5
