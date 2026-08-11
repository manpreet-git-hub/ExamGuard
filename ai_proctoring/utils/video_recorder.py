# ── utils/video_recorder.py — Violation video clip recorder ──────────────────
#
#  Records short video clips (PRE + POST violation window) for each violation
#  type instead of static screenshots.
#
#  Strategy: maintains a rolling frame buffer (ring buffer) so that when a
#  violation is confirmed we can write the seconds BEFORE the trigger as well
#  as continue recording for a post-trigger window — giving reviewers full
#  context.
#
#  Recording lifecycle:
#    1.  Every frame is pushed into the rolling PRE-buffer via push_frame().
#    2.  When a violation is confirmed, start_recording() is called. The
#        pre-buffer frames are flushed first, then live frames are captured
#        until the POST_SECONDS window expires.
#    3.  stop_recording() finalises and releases the VideoWriter.

import os
import time
import threading
import collections
from datetime import datetime

import cv2
import streamlit as st

try:
    from ai_proctoring.config import EVIDENCE_DIR, VTYPE_META
    from ai_proctoring.utils.logger import log_evidence_row
except ImportError:
    from config import EVIDENCE_DIR, VTYPE_META
    from utils.logger import log_evidence_row

# ── Tunable constants ──────────────────────────────────────────────────────────
FPS           = 20          # output clip framerate
PRE_SECONDS   = 3           # seconds of pre-violation footage to include
POST_SECONDS  = 5           # seconds of post-violation footage to capture
MAX_CLIP_SEC  = PRE_SECONDS + POST_SECONDS  # total max clip length
VIDEO_COOLDOWN = 10.0       # minimum seconds between clips of the same type

# ── Module-level state (one recorder per process) ─────────────────────────────
_pre_buffer: collections.deque = collections.deque(
    maxlen=int(PRE_SECONDS * FPS)
)
_active_writers: dict = {}       # vtype → {"writer": VideoWriter, "end_time": float, "path": str}
_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def push_frame(frame):
    """
    Push a raw BGR frame into the rolling pre-violation buffer.
    Must be called every frame regardless of whether a violation is active.
    Also feeds any currently-open writers.
    """
    small = _resize(frame)
    with _lock:
        _pre_buffer.append(small.copy())
        _flush_to_writers(small)


def start_recording(violation_type: str) -> str | None:
    """
    Begin recording a violation clip for *violation_type*.

    If a clip for this type is already recording, this call is a no-op.
    Enforces VIDEO_COOLDOWN between clips of the same type.

    Args:
        violation_type: key from VTYPE_META (e.g. "phone", "looking_away").

    Returns:
        Output filepath if a new recording was started, else None.
    """
    now = time.time()

    # Cooldown check via session state
    cooldowns = st.session_state.setdefault("video_cooldowns", {})
    if now - cooldowns.get(violation_type, 0) < VIDEO_COOLDOWN:
        return None

    with _lock:
        if violation_type in _active_writers:
            return None   # already recording this type

        filepath = _build_filepath(violation_type)
        writer   = _open_writer(filepath)
        if writer is None:
            return None

        # Write pre-buffer frames first
        for f in list(_pre_buffer):
            writer.write(f)

        _active_writers[violation_type] = {
            "writer":   writer,
            "end_time": now + POST_SECONDS,
            "path":     filepath,
            "vtype":    violation_type,
        }
        cooldowns[violation_type] = now

    return filepath


def flush_writers():
    """
    Finalise any recordings whose post-violation window has expired.
    Call this once per frame from the main camera loop.
    """
    now      = time.time()
    finished = []
    with _lock:
        for vtype, rec in list(_active_writers.items()):
            if now >= rec["end_time"]:
                finished.append(vtype)

    for vtype in finished:
        _close_writer(vtype)


def stop_all():
    """Force-close every active writer (call on session end / reset)."""
    with _lock:
        vtypes = list(_active_writers.keys())
    for vtype in vtypes:
        _close_writer(vtype)


def is_recording(violation_type: str) -> bool:
    with _lock:
        return violation_type in _active_writers


# ─────────────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resize(frame, width=640):
    """Resize frame to fixed width, preserving aspect ratio."""
    h, w = frame.shape[:2]
    if w == width:
        return frame
    scale  = width / w
    height = int(h * scale)
    return cv2.resize(frame, (width, height))


def _build_filepath(violation_type: str) -> str:
    ts_str  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sid     = st.session_state.session_id
    vslug   = violation_type.replace(" ", "_")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    return os.path.join(EVIDENCE_DIR, f"{sid}_{vslug}_{ts_str}.mp4")


def _open_writer(filepath: str):
    """Create an OpenCV VideoWriter for an MP4 file."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(filepath, fourcc, FPS, (640, 480))
    if not writer.isOpened():
        # Fallback: try AVI with XVID
        filepath_avi = filepath.replace(".mp4", ".avi")
        fourcc  = cv2.VideoWriter_fourcc(*"XVID")
        writer  = cv2.VideoWriter(filepath_avi, fourcc, FPS, (640, 480))
        if not writer.isOpened():
            return None
    return writer


def _flush_to_writers(frame):
    """Write *frame* to all active writers (must be called under _lock)."""
    now = time.time()
    for rec in _active_writers.values():
        if now < rec["end_time"]:
            rec["writer"].write(frame)


def _close_writer(vtype: str):
    """Finalise, release, and log the completed clip."""
    with _lock:
        rec = _active_writers.pop(vtype, None)
    if rec is None:
        return

    rec["writer"].release()
    filepath = rec["path"]
    filename = os.path.basename(filepath)
    label, _ = VTYPE_META.get(vtype, (vtype.upper(), (0, 51, 255)))

    record = {
        "path":     filepath,
        "filename": filename,
        "vtype":    vtype,
        "label":    label,
        "ts":       datetime.now().strftime("%H:%M:%S"),
        "ts_iso":   datetime.now().isoformat(),
        "score":    st.session_state.get("integrity_score", "—"),
        "media":    "video",                    # distinguish from screenshots
        "duration": PRE_SECONDS + POST_SECONDS,
    }

    evidence_log = st.session_state.setdefault("evidence_log", [])
    evidence_log.append(record)
    log_evidence_row(record)
