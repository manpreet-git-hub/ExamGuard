# ── config.py — Constants, thresholds, and penalties ──────────────────────────

import os

# ── Evidence / Video Recording ─────────────────────────────────────────────────
# Violations now produce short video clips instead of static screenshots.
# See utils/video_recorder.py for full implementation.
VIDEO_PRE_SECONDS  = 3     # seconds of footage BEFORE the violation trigger
VIDEO_POST_SECONDS = 5     # seconds of footage AFTER the violation trigger
VIDEO_COOLDOWN     = 10.0  # min seconds between clips of the same violation type
EVIDENCE_DIR       = "evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# Legacy alias — kept so any code that still imports SCREENSHOT_COOLDOWN doesn't break
SCREENSHOT_COOLDOWN = VIDEO_COOLDOWN

# ── Integrity Score ────────────────────────────────────────────────────────────
PENALTIES = {
    "multi_face":     25,
    "no_face":        15,
    "phone":          30,
    "laptop":         25,   # laptop detected on camera
    "looking_away":   10,   # head-pose violation
    "eye_gaze_away":   8,   # eye-gaze violation (L / R / Up / Down)
    "talking":         8,
}
PERSIST_THRESHOLD = 2.5   # seconds a violation must persist before penalty deducted
REARM_COOLDOWN    = 8.0   # seconds before same violation can trigger again
MIN_SCORE         = 0

# ── Eye Gaze ───────────────────────────────────────────────────────────────────
# Directions treated as "looking away" violations
EYE_GAZE_AWAY_DIRECTIONS = {"Looking Left", "Looking Right", "Looking Up", "Looking Down"}

# ── Mediapipe / YOLO thresholds ────────────────────────────────────────────────
FACE_DETECTION_CONFIDENCE = 0.75
FACE_MESH_MAX_FACES       = 5
FACE_MESH_DETECTION_CONF  = 0.5
FACE_MESH_TRACKING_CONF   = 0.5

# ── Tab / Window switching detection ──────────────────────────────────────────
TAB_SWITCH_WARNING_ONLY  = 3    # first 3 switches: warning only, no deduction
TAB_SWITCH_PENALTY_FROM  = 4    # 4th+ switch: deduct full penalty
TAB_SWITCH_PENALTY       = 100  # integrity points deducted on 4th+ violation
TAB_SWITCH_THRESHOLD     = 4    # violations at which session is flagged
TAB_SWITCH_REARM         = 5.0  # seconds min between successive penalties
TAB_EVENT_FILE           = ".tab_events.json"
TAB_RESET_FILE           = ".tab_reset.flag"
TAB_SESSION_FILE         = ".tab_session.flag"

# ── Evidence metadata ──────────────────────────────────────────────────────────
VTYPE_META = {
    "multi_face":        ("Multiple Faces Detected", (0,   51, 255)),
    "no_face":           ("No Face Detected",         (0,   51, 255)),
    "phone":             ("Phone Detected",           (0,   51, 255)),
    "laptop":            ("Laptop Detected",          (0,  100, 255)),
    "looking_away":      ("Looking Away",             (0,  200, 255)),
    "eye_gaze_away":     ("Suspicious Eye Movement",  (0,  200, 255)),
    "talking":           ("Talking Detected",         (0,  200, 255)),
    "identity_mismatch": ("Identity Mismatch",        (0,   51, 255)),
    "tab_switch":        ("Tab Switch Detected",      (0,  140, 255)),
    "window_blur":       ("Window Focus Lost",        (0,  140, 255)),
}