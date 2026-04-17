# ── engine/frame_processor.py — Run all detection modules on a single frame ────

import cv2

try:
    from ai_proctoring.detection.face_detection import draw_face_box
    from ai_proctoring.detection.eye_tracking import get_eye_direction
    from ai_proctoring.detection.head_pose import get_head_pose
    from ai_proctoring.detection.opencv_fallback import detect_with_cascades
    from ai_proctoring.detection.talking_detection import detect_talking
    from ai_proctoring.detection.phone_detection import detect_devices
    from ai_proctoring.runtime_state import get_state
    from ai_proctoring.utils.video_recorder import push_frame, flush_writers
except ImportError:
    from detection.face_detection    import draw_face_box
    from detection.eye_tracking      import get_eye_direction
    from detection.head_pose         import get_head_pose
    from detection.opencv_fallback   import detect_with_cascades
    from detection.talking_detection import detect_talking
    from detection.phone_detection   import detect_devices
    from runtime_state               import get_state
    from utils.video_recorder        import push_frame, flush_writers

# Gaze directions that count as "looking away"
_AWAY_GAZES = {"Looking Left", "Looking Right", "Looking Up", "Looking Down"}

# Colour map for on-frame gaze label
_GAZE_COLORS = {
    "Looking Center": (0, 255, 136),
    "Looking Left":   (0, 200, 255),
    "Looking Right":  (0, 200, 255),
    "Looking Up":     (255, 180,  0),
    "Looking Down":   (255, 180,  0),
}


def process_frame(frame, models):
    """
    Run all detection modules on a BGR frame.

    Args:
        frame:  BGR numpy array from OpenCV.
        models: dict returned by load_models() containing any subset of
                "face_det", "face_mesh", "yolo".

    Returns:
        tuple: (annotated_frame, results_dict)
            annotated_frame: BGR frame with visual overlays drawn.
            results_dict: {
                "head":       str,   # head direction label
                "head_state": str,   # "ok" | "warn" | "alert" | "none"
                "eye":        str,   # gaze label  (L/R/Up/Down/Center)
                "eye_state":  str,   # "ok" | "warn" | "none"
                "talking":    bool,
                "phone":      bool,
                "laptop":     bool,
                "num_faces":  int,
                "suspicion":  int,   # 0–100
                "face_confs": list,
            }
    """
    results = {
        "head":       "Unknown",
        "head_state": "none",
        "eye":        "Unknown",
        "eye_state":  "none",
        "talking":    False,
        "phone":      False,
        "laptop":     False,
        "num_faces":  0,
        "suspicion":  0,
        "face_confs": [],
    }

    rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = frame.shape[:2]

    # ── Face detection ───────────────────────────────────────────────────────
    if "face_det" in models:
        det_results = models["face_det"].process(rgb)
        if det_results.detections:
            results["num_faces"] = len(det_results.detections)
            for det in det_results.detections:
                box   = det.location_data.relative_bounding_box
                bx    = int(box.xmin  * w)
                by    = int(box.ymin  * h)
                bw    = int(box.width * w)
                bh    = int(box.height * h)
                conf  = det.score[0]
                susp  = results["suspicion"]
                color = (
                    (0, 255, 136) if susp < 25
                    else (0, 204, 255) if susp < 60
                    else (51, 51, 255)
                )
                draw_face_box(frame, bx, by, bw, bh, color, conf)
    elif "cv_face_cascade" in models:
        fallback = detect_with_cascades(
            frame,
            models["cv_face_cascade"],
            models.get("cv_eye_cascade"),
        )
        results["num_faces"] = fallback["num_faces"]
        for (bx, by, bw, bh) in fallback["faces"]:
            draw_face_box(frame, bx, by, bw, bh, (0, 255, 136), 0.6)
        results["head"] = fallback["head"]
        results["head_state"] = fallback["head_state"]
        results["eye"] = fallback["eye"]
        results["eye_state"] = fallback["eye_state"]

    # ── Face mesh (head pose, eye tracking, talking) ─────────────────────────
    if "face_mesh" in models:
        mesh_results = models["face_mesh"].process(rgb)
        if mesh_results.multi_face_landmarks:
            face_lms = mesh_results.multi_face_landmarks[0]
            face     = [[int(lm.x * w), int(lm.y * h)] for lm in face_lms.landmark]

            head_text, head_state = get_head_pose(face)

            # get_eye_direction now returns (label, state)
            eye_text, eye_state = get_eye_direction(face)

            talking = detect_talking(face)

            results.update({
                "head":       head_text,
                "head_state": head_state,
                "eye":        eye_text,
                "eye_state":  eye_state,
                "talking":    talking,
            })

            # Head pose overlay
            head_color = (
                (0, 255, 136) if head_state == "ok"
                else (0, 220, 255) if head_state == "warn"
                else (51, 51, 255)
            )
            cv2.putText(
                frame, head_text, (w // 2 - 80, 36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, head_color, 2, cv2.LINE_AA,
            )

            # Gaze direction overlay — always visible, colour-coded
            gaze_color = _GAZE_COLORS.get(eye_text, (200, 200, 200))
            cv2.putText(
                frame, f"Gaze: {eye_text}", (10, h - 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, gaze_color, 2, cv2.LINE_AA,
            )

            if talking:
                cv2.putText(
                    frame, "TALKING DETECTED", (20, h - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (51, 51, 255), 2, cv2.LINE_AA,
                )

    # ── Device detection (phone + laptop via YOLOv8x) ───────────────────────
    if "yolo" in models:
        devices = detect_devices(frame, models["yolo"])
        results["phone"]  = devices["phone"]
        results["laptop"] = devices["laptop"]

        if devices["laptop"]:
            cv2.putText(
                frame, "LAPTOP DETECTED", (w - 230, h - 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2, cv2.LINE_AA,
            )

    # ── Push frame into pre-violation rolling buffer + flush finished clips ──
    push_frame(frame)
    flush_writers()

    # ── Suspicion score ──────────────────────────────────────────────────────
    s = 0
    if results["num_faces"] > 1:
        s += 50
    if results["phone"]:
        s += 30
    if results["laptop"]:
        s += 25
    if results["head_state"] in ("warn", "alert"):
        s += 5 if results["head_state"] == "warn" else 15
    if results["eye_state"] == "warn":
        s += 10
    if results["talking"]:
        s += 20
    results["suspicion"] = min(100, s)

    # ── Warning banners on frame ─────────────────────────────────────────────
    if results["num_faces"] > 1:
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 200), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        cv2.putText(
            frame, "MULTIPLE FACES DETECTED", (w // 2 - 160, 32),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
        )

    if results["num_faces"] == 0:
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 180), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        cv2.putText(
            frame, "NO FACE DETECTED", (w // 2 - 120, 32),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
        )

    # Gaze-away banner — show centred label when not looking at screen
    if results["eye"] in _AWAY_GAZES:
        gaze_c = _GAZE_COLORS.get(results["eye"], (0, 200, 255))
        cv2.putText(
            frame, f"GAZE: {results['eye'].upper()}", (w // 2 - 120, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, gaze_c, 2, cv2.LINE_AA,
        )

    # ── Session ID watermark ─────────────────────────────────────────────────
    session_id = get_state("session_id", "BACKEND")
    cv2.putText(
        frame, f"SESSION: {session_id}", (10, h - 15),
        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (60, 90, 100), 1,
    )

    return frame, results
