# ── models/model_loader.py — Load Mediapipe + YOLO models ─────────────────────

from functools import lru_cache
import logging

# ── Graceful imports ───────────────────────────────────────────────────────────
try:
    import mediapipe as mp
    MEDIAPIPE_OK = True
except ImportError:
    MEDIAPIPE_OK = False

try:
    from ultralytics import YOLO
    YOLO_OK = True
except ImportError:
    YOLO_OK = False

from config import (
    FACE_DETECTION_CONFIDENCE,
    FACE_MESH_MAX_FACES,
    FACE_MESH_DETECTION_CONF,
    FACE_MESH_TRACKING_CONF,
)
from detection.opencv_fallback import load_cascades

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_models():
    """Load and cache all ML models. Returns a dict of model handles."""
    models = {}
    models.update(load_cascades())

    if MEDIAPIPE_OK:
        mp_face = mp.solutions.face_detection
        mp_mesh = mp.solutions.face_mesh
        try:
            models["face_det"] = mp_face.FaceDetection(
                min_detection_confidence=FACE_DETECTION_CONFIDENCE
            )
        except Exception as exc:
            logger.warning("MediaPipe face detection unavailable: %s", exc)
        try:
            models["face_mesh"] = mp_mesh.FaceMesh(
                max_num_faces=FACE_MESH_MAX_FACES,
                refine_landmarks=True,
                min_detection_confidence=FACE_MESH_DETECTION_CONF,
                min_tracking_confidence=FACE_MESH_TRACKING_CONF,
            )
        except Exception as exc:
            logger.warning("MediaPipe face mesh unavailable: %s", exc)

    if YOLO_OK:
        # Try yolov8x (most accurate) first, fall back to progressively smaller models
        for model_name in ("yolov8x.pt", "yolov8l.pt", "yolov8m.pt", "yolov8n.pt"):
            try:
                models["yolo"] = YOLO(model_name)
                models["yolo_model_name"] = model_name   # expose for UI display
                break
            except Exception as exc:
                logger.warning("YOLO model %s unavailable: %s", model_name, exc)
                continue

    return models
