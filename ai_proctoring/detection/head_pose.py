# ── detection/head_pose.py — Head pose estimation ─────────────────────────────


def get_head_pose(face):
    """
    Estimate head orientation from key facial landmarks.

    Args:
        face: list of [x, y] pixel coordinates for all FaceMesh landmarks.

    Returns:
        tuple: (direction_str, state_str)
            direction_str: "Looking Center" | "Looking Right" | "Looking Left" |
                           "Looking Down"  | "Looking Up"
            state_str:     "ok" | "warn" | "alert"
    """
    nose      = face[4]
    left_eye  = face[33]
    right_eye = face[263]
    chin      = face[152]

    eye_cx = (left_eye[0] + right_eye[0]) // 2
    eye_cy = (left_eye[1] + right_eye[1]) // 2
    face_w = abs(right_eye[0] - left_eye[0])
    face_h = abs(chin[1] - eye_cy)
    thresh = face_w * 0.25

    if nose[0] > eye_cx + thresh:
        return "Looking Right", "warn"
    if nose[0] < eye_cx - thresh:
        return "Looking Left", "warn"
    if face_h > 0 and nose[1] - eye_cy > face_h * 0.45:
        return "Looking Down", "alert"
    if face_h > 0 and nose[1] - eye_cy < -face_h * 0.15:
        return "Looking Up", "alert"
    return "Looking Center", "ok"
