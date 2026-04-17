import cv2


def load_cascades():
    base = getattr(cv2.data, "haarcascades", "")
    if not base:
        return {}

    face_path = f"{base}haarcascade_frontalface_default.xml"
    eye_path = f"{base}haarcascade_eye.xml"

    face_cascade = cv2.CascadeClassifier(face_path)
    eye_cascade = cv2.CascadeClassifier(eye_path)

    models = {}
    if not face_cascade.empty():
        models["cv_face_cascade"] = face_cascade
    if not eye_cascade.empty():
        models["cv_eye_cascade"] = eye_cascade
    return models


def detect_with_cascades(frame, face_cascade, eye_cascade=None):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )

    result = {
        "faces": [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces],
        "num_faces": len(faces),
        "head": "Unknown",
        "head_state": "none",
        "eye": "Unknown",
        "eye_state": "none",
    }

    if len(faces) == 0:
        result["head"] = "No Face"
        result["eye"] = "Eyes not visible"
        result["eye_state"] = "warn"
        return result

    x, y, w, h = max(faces, key=lambda item: item[2] * item[3])
    frame_h, frame_w = frame.shape[:2]
    face_center_x = x + w / 2
    face_center_y = y + h / 2

    x_offset_ratio = (face_center_x - (frame_w / 2)) / max(w, 1)
    y_offset_ratio = (face_center_y - (frame_h / 2)) / max(h, 1)

    if x_offset_ratio > 0.18:
        result["head"] = "Looking Right"
        result["head_state"] = "warn"
    elif x_offset_ratio < -0.18:
        result["head"] = "Looking Left"
        result["head_state"] = "warn"
    elif y_offset_ratio > 0.18:
        result["head"] = "Looking Down"
        result["head_state"] = "alert"
    elif y_offset_ratio < -0.18:
        result["head"] = "Looking Up"
        result["head_state"] = "alert"
    else:
        result["head"] = "Looking Center"
        result["head_state"] = "ok"

    if eye_cascade is not None:
        roi = gray[y:y + int(h * 0.55), x:x + w]
        eyes = eye_cascade.detectMultiScale(
            roi,
            scaleFactor=1.1,
            minNeighbors=6,
            minSize=(18, 18),
        )
        if len(eyes) >= 1:
            result["eye"] = "Looking Center"
            result["eye_state"] = "ok"
        else:
            result["eye"] = "Eyes not visible"
            result["eye_state"] = "warn"

    return result
