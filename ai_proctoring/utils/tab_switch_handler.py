# ── utils/tab_switch_handler.py ───────────────────────────────────────────────
"""
Tab / Window Switching Detection — Backend Handler

Penalty logic (per requirements)
----------------------------------
  Switches 1-3  → warning toast only, NO score deduction
  Switch 4+     → deduct 100 integrity points per event, flag session
  Score hits 0  → terminate exam immediately, show cheating screen
"""

import json
import os
import time
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import streamlit as st

from config import (
    TAB_SWITCH_PENALTY,
    TAB_SWITCH_PENALTY_FROM,
    TAB_SWITCH_THRESHOLD,
    TAB_SWITCH_REARM,
    TAB_EVENT_FILE,
    TAB_RESET_FILE,
    TAB_SESSION_FILE,
    PENALTIES,
)
from utils.logger import log_event

PENALTIES["tab_switch"]  = TAB_SWITCH_PENALTY
PENALTIES["window_blur"] = TAB_SWITCH_PENALTY

_SERVER_PORT = 8765


class _TabEventHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length  = int(self.headers.get("Content-Length", 0))
            body    = self.rfile.read(length)
            payload = json.loads(body)

            existing = []
            if os.path.exists(TAB_EVENT_FILE):
                try:
                    with open(TAB_EVENT_FILE) as f:
                        existing = json.load(f)
                except Exception:
                    existing = []
            existing.append(payload)
            with open(TAB_EVENT_FILE, "w") as f:
                json.dump(existing, f)

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        except Exception:
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        """JS polls GET to get reset signal and session-active status."""
        reset  = os.path.exists(TAB_RESET_FILE)
        active = os.path.exists(TAB_SESSION_FILE)
        if reset:
            try:
                os.remove(TAB_RESET_FILE)
            except Exception:
                pass
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        resp = ('{"reset":true,"active":true}' if reset
                else f'{{"reset":false,"active":{"true" if active else "false"}}}')
        self.wfile.write(resp.encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, *args):
        pass


@st.cache_resource
def _start_event_server():
    server = HTTPServer(("127.0.0.1", _SERVER_PORT), _TabEventHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return _SERVER_PORT


def init_tab_state():
    _start_event_server()
    if "tab_switch_count"    not in st.session_state: st.session_state.tab_switch_count    = 0
    if "tab_switch_log"      not in st.session_state: st.session_state.tab_switch_log      = []
    if "tab_switch_flagged"  not in st.session_state: st.session_state.tab_switch_flagged  = False
    if "_last_tab_penalty"   not in st.session_state: st.session_state._last_tab_penalty   = 0.0
    if "_tab_seen_ids"       not in st.session_state: st.session_state._tab_seen_ids       = set()
    if "exam_terminated"     not in st.session_state: st.session_state.exam_terminated     = False


def set_session_active(active: bool):
    """Write or remove the session-active flag file that JS polls."""
    try:
        if active:
            with open(TAB_SESSION_FILE, "w") as f:
                f.write("1")
        else:
            if os.path.exists(TAB_SESSION_FILE):
                os.remove(TAB_SESSION_FILE)
    except Exception:
        pass


def reset_tab_state():
    st.session_state.tab_switch_count    = 0
    st.session_state.tab_switch_log      = []
    st.session_state.tab_switch_flagged  = False
    st.session_state._last_tab_penalty   = 0.0
    st.session_state._tab_seen_ids       = set()
    st.session_state.exam_terminated     = False
    # Write reset signal so JS clears its local counter
    try:
        with open(TAB_RESET_FILE, "w") as f:
            f.write("reset")
    except Exception:
        pass
    # Clear any stale events and session flag
    try:
        if os.path.exists(TAB_EVENT_FILE):
            os.remove(TAB_EVENT_FILE)
    except Exception:
        pass
    set_session_active(False)


def process_tab_events(current_frame=None):
    """
    Drain the event file and apply penalty rules.
    Called every camera frame (~30 fps).

    Rules:
      count 1-3  → log warning, no score deduction
      count 4+   → deduct 100 pts, flag session, capture screenshot
      score == 0 → set exam_terminated = True (caller breaks the loop)
    """
    if not os.path.exists(TAB_EVENT_FILE):
        return []

    try:
        with open(TAB_EVENT_FILE) as f:
            events = json.load(f)
        os.remove(TAB_EVENT_FILE)
    except Exception:
        return []

    now       = time.time()
    processed = []

    for evt in events:
        uid = evt.get("id", "")
        if uid and uid in st.session_state._tab_seen_ids:
            continue
        if uid:
            st.session_state._tab_seen_ids.add(uid)

        vtype = evt.get("type", "tab_switch")
        ts    = evt.get("ts", datetime.now().isoformat())

        st.session_state.tab_switch_count += 1
        count = st.session_state.tab_switch_count

        label_map = {
            "tab_switch":  "Tab switch detected",
            "window_blur": "Window focus lost",
        }
        human_label = label_map.get(vtype, "Focus violation")

        penalty = 0
        if count >= TAB_SWITCH_PENALTY_FROM:
            last = st.session_state._last_tab_penalty
            if now - last >= TAB_SWITCH_REARM:
                penalty = TAB_SWITCH_PENALTY
                st.session_state.integrity_score = max(
                    0, st.session_state.integrity_score - penalty
                )
                st.session_state._last_tab_penalty = now

        entry = {
            "vtype":   vtype,
            "label":   human_label,
            "ts":      datetime.now().strftime("%H:%M:%S"),
            "ts_iso":  ts,
            "score":   st.session_state.integrity_score,
            "penalty": penalty,
            "count":   count,
        }
        st.session_state.tab_switch_log.append(entry)
        log_event(human_label, penalty)

        if penalty > 0 and current_frame is not None:
            try:
                from utils.evidence import capture_evidence
                capture_evidence(current_frame, vtype)
            except Exception:
                pass

        if count >= TAB_SWITCH_THRESHOLD:
            st.session_state.tab_switch_flagged = True

        # Terminate exam if score has hit zero
        if st.session_state.integrity_score <= 0:
            st.session_state.exam_terminated = True

        processed.append(entry)

    return processed