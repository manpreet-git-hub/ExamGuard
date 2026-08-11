# ── detection/face_detection.py — Face detection helpers ──────────────────────

import cv2


def draw_face_box(frame, x, y, w, h, color, conf):
    """
    Draw fancy corner-bracket bounding box and confidence label on frame.

    Args:
        frame:  BGR numpy array (modified in-place).
        x, y:   Top-left corner of the bounding box (pixels).
        w, h:   Width and height of the bounding box (pixels).
        color:  BGR tuple for box and label colour.
        conf:   Detection confidence float (0–1).
    """
    x2, y2 = x + w, y + h
    L, T   = min(40, w // 3), 3

    cv2.rectangle(frame, (x, y), (x2, y2), color, 1)

    for (px, py, dx, dy) in [
        (x,  y,   1,  1),
        (x2, y,  -1,  1),
        (x,  y2,  1, -1),
        (x2, y2, -1, -1),
    ]:
        cv2.line(frame, (px, py), (px + dx * L, py), color, T)
        cv2.line(frame, (px, py), (px, py + dy * L), color, T)

    cv2.putText(
        frame, f"FACE {int(conf * 100)}%", (x, y - 8),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA,
    )
