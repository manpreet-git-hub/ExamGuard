# ── detection/phone_detection.py — Advanced YOLO object detection ─────────────
#
#  Uses YOLOv8x (extra-large, most accurate) to detect:
#   • cell phone  — COCO class 67
#   • laptop      — COCO class 63
#
#  Returns a dict so the caller can distinguish between the two device types.

import cv2

# COCO class names of interest and their display config
_TARGETS = {
    "cell phone": {"label": "PHONE",  "color": (51,  51, 255), "key": "phone"},
    "laptop":     {"label": "LAPTOP", "color": (0,  100, 255), "key": "laptop"},
}


def detect_devices(frame, yolo_model):
    """
    Run YOLOv8x inference and detect phones and laptops.

    Draws annotated bounding boxes on the frame in-place.

    Args:
        frame:      BGR numpy array (modified in-place).
        yolo_model: Loaded Ultralytics YOLO model instance (should be yolov8x).

    Returns:
        dict: {
            "phone":  bool,  # True if ≥1 cell phone detected
            "laptop": bool,  # True if ≥1 laptop detected
        }
    """
    found = {"phone": False, "laptop": False}

    results = yolo_model(frame, verbose=False)

    for box in results[0].boxes:
        cls_name = yolo_model.names[int(box.cls[0])].lower()
        if cls_name not in _TARGETS:
            continue

        meta = _TARGETS[cls_name]
        found[meta["key"]] = True

        conf = float(box.conf[0])
        bx1, by1, bx2, by2 = map(int, box.xyxy[0])

        cv2.rectangle(frame, (bx1, by1), (bx2, by2), meta["color"], 2)
        cv2.putText(
            frame,
            f"{meta['label']} {conf:.0%}",
            (bx1, by1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, meta["color"], 2,
        )

    return found


# ── Legacy wrapper so existing callers work unchanged ─────────────────────────
def detect_phone(frame, yolo_model):
    """Thin wrapper kept for backward-compatibility. Returns bool."""
    return detect_devices(frame, yolo_model)["phone"]
