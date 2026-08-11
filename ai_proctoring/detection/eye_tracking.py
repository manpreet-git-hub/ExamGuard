# ── detection/eye_tracking.py — Eye gaze direction detection (L/R/Up/Down) ───


def get_eye_direction(face):
    """
    Determine gaze direction using MediaPipe FaceMesh iris landmarks.

    Uses BOTH horizontal (left/right) and vertical (up/down) iris ratios
    from the LEFT eye to determine where the subject is looking.

    MediaPipe landmark indices used:
      Left eye corners : 33 (inner), 133 (outer)
      Left eye top/bot : 159 (top eyelid midpoint), 145 (bottom eyelid midpoint)
      Left iris center : 468  (requires refine_landmarks=True)

    Args:
        face: list of [x, y] pixel coordinates for all 478 FaceMesh landmarks.

    Returns:
        tuple: (direction_str, eye_state_str)
            direction_str : "Looking Center" | "Looking Left" | "Looking Right"
                            | "Looking Up"   | "Looking Down"
            eye_state_str : "ok" | "warn"
    """
    # ── Landmarks ─────────────────────────────────────────────────────────────
    left_corner  = face[33]    # inner (nose-side) corner of left eye
    right_corner = face[133]   # outer corner of left eye
    iris         = face[468]   # left iris centre (requires refine_landmarks)
    eye_top      = face[159]   # top eyelid centre
    eye_bottom   = face[145]   # bottom eyelid centre

    eye_width  = right_corner[0] - left_corner[0]
    eye_height = eye_bottom[1]   - eye_top[1]

    if eye_width == 0 or eye_height == 0:
        return "Looking Center", "ok"

    # Normalised ratios in [0, 1]
    h_ratio = (iris[0] - left_corner[0]) / eye_width   # 0 = far left, 1 = far right
    v_ratio = (iris[1] - eye_top[1])     / eye_height  # 0 = top, 1 = bottom

    # ── Thresholds ─────────────────────────────────────────────────────────────
    H_LEFT_THRESH  = 0.35   # iris < this  → "Looking Right" (frame is flipped)
    H_RIGHT_THRESH = 0.65   # iris > this  → "Looking Left"  (frame is flipped)
    V_UP_THRESH    = 0.40   # iris < this  → "Looking Up"
    V_DOWN_THRESH  = 0.68   # iris > this  → "Looking Down"

    # Vertical check takes priority (avoids diagonal label confusion)
    if v_ratio < V_UP_THRESH:
        return "Looking Up",    "warn"
    if v_ratio > V_DOWN_THRESH:
        return "Looking Down",  "warn"
    if h_ratio < H_LEFT_THRESH:
        return "Looking Right", "warn"   # mirrored — webcam frame is flipped
    if h_ratio > H_RIGHT_THRESH:
        return "Looking Left",  "warn"   # mirrored

    return "Looking Center", "ok"
