"""
app.py — AI Proctoring System — Main Streamlit entry point.

Run with:
    streamlit run app.py
"""

import os
import time
import cv2
from collections import deque
from datetime import datetime

import streamlit as st

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="AI Proctoring System",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Graceful import warnings ───────────────────────────────────────────────────
try:
    import mediapipe  # noqa: F401
except ImportError:
    st.warning("mediapipe not installed. Run: pip install mediapipe")

# ── Project imports ────────────────────────────────────────────────────────────
from config import PENALTIES, EVIDENCE_DIR
from model_loader import load_models
from engine.frame_processor import process_frame
from engine.scoring_engine import (
    update_integrity_score,
    generate_final_report,
    severity_label,
)
from ui.gauges  import gauge_svg, integrity_score_svg
from ui.sensors import sensor_html
from ui.charts  import bar_chart_html
from ui.panels  import evidence_panel_html, tab_switch_banner_html, tab_switch_log_html
from utils.tab_switch_handler import init_tab_state, reset_tab_state, process_tab_events, set_session_active

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

/* Global */
html, body, [class*="css"] { font-family: 'Syne', sans-serif !important; }
.stApp { background: #080c10; color: #e8f0f5; }
.block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Metric cards */
div[data-testid="metric-container"] {
    background: #0d1318;
    border: 1px solid #1a2530;
    border-radius: 12px;
    padding: 14px 18px;
    position: relative;
    overflow: hidden;
}
div[data-testid="metric-container"]::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,212,255,0.3), transparent);
}
div[data-testid="metric-container"] label { color: #7a95a5 !important; font-size: 11px !important; letter-spacing: 2px !important; text-transform: uppercase !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-family: 'Space Mono', monospace !important; font-size: 18px !important; }

/* Section headers */
.section-title {
    font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
    color: #7a95a5; margin-bottom: 10px; font-weight: 700;
    font-family: 'Space Mono', monospace;
}

/* Status badge */
.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px; border-radius: 20px;
    font-size: 12px; font-weight: 700; letter-spacing: 1px;
    font-family: 'Space Mono', monospace;
}
.badge-green  { background: rgba(0,255,136,0.08); border: 1px solid rgba(0,255,136,0.35); color: #00ff88; }
.badge-yellow { background: rgba(255,204,0,0.08); border: 1px solid rgba(255,204,0,0.35); color: #ffcc00; }
.badge-red    { background: rgba(255,51,85,0.08);  border: 1px solid rgba(255,51,85,0.35);  color: #ff3355; }
.badge-gray   { background: rgba(74,96,112,0.2);   border: 1px solid #1a2530;              color: #4a6070; }

/* Sensor card */
.sensor-card {
    background: #0d1318; border: 1px solid #1a2530;
    border-radius: 12px; padding: 14px 16px;
    position: relative; overflow: hidden;
}
.sensor-card-active { border-color: rgba(0,212,255,0.3);  background: rgba(0,212,255,0.03); }
.sensor-card-warn   { border-color: rgba(255,204,0,0.35); background: rgba(255,204,0,0.03); }
.sensor-card-alert  { border-color: rgba(255,51,85,0.35); background: rgba(255,51,85,0.03); }
.sensor-label { font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; color: #4a6070; margin-bottom: 4px; }
.sensor-value-g { font-size: 15px; font-weight: 700; color: #00ff88; }
.sensor-value-c { font-size: 15px; font-weight: 700; color: #00d4ff; }
.sensor-value-y { font-size: 15px; font-weight: 700; color: #ffcc00; }
.sensor-value-r { font-size: 15px; font-weight: 700; color: #ff3355; }
.sensor-value-m { font-size: 15px; font-weight: 700; color: #7a95a5; }

/* Log item */
.log-item {
    display: flex; align-items: center; gap: 10px;
    padding: 7px 10px; background: rgba(0,0,0,0.2);
    border: 1px solid #1a2530; border-radius: 8px;
    font-size: 11px; margin-bottom: 6px;
    font-family: 'Space Mono', monospace;
}
.log-dot-r { width: 7px; height: 7px; border-radius: 50%; background: #ff3355; display:inline-block; flex-shrink:0; }
.log-dot-y { width: 7px; height: 7px; border-radius: 50%; background: #ffcc00; display:inline-block; flex-shrink:0; }
.log-text  { flex: 1; color: #7a95a5; }
.log-time  { color: #4a6070; font-size: 10px; }

/* Alert banner */
.alert-banner {
    padding: 12px 20px; border-radius: 10px;
    background: rgba(255,51,85,0.08);
    border: 1px solid rgba(255,51,85,0.35);
    color: #ff3355; font-weight: 700; font-size: 13px;
    margin-bottom: 14px;
}

/* Divider */
hr { border-color: #1a2530 !important; margin: 10px 0 !important; }

/* Progress bar colors */
.stProgress > div > div { background: #1a2530 !important; border-radius: 4px !important; }
.stProgress > div > div > div { border-radius: 4px !important; }

/* Buttons */
.stButton > button {
    background: rgba(0,212,255,0.08) !important;
    border: 1.5px solid rgba(0,212,255,0.35) !important;
    color: #00d4ff !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 12px !important;
    letter-spacing: 1px !important; border-radius: 8px !important;
}
.stButton > button:hover { background: rgba(0,212,255,0.18) !important; }

/* Camera frame */
.cam-frame {
    background: #050a0e; border: 1px solid #1a2530;
    border-radius: 10px; overflow: hidden;
}

/* Tab-switch toast notification */
@keyframes tsSlideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to   { transform: translateY(0);     opacity: 1; }
}
#ts-toast {
    position: fixed; top: 18px; left: 50%; transform: translateX(-50%);
    z-index: 99999; min-width: 360px; max-width: 520px;
    background: rgba(255,204,0,0.12);
    border: 1.5px solid rgba(255,204,0,0.5);
    border-radius: 10px; padding: 12px 20px;
    font-family: 'Space Mono', monospace; font-size: 12px;
    color: #ffcc00; font-weight: 700; letter-spacing: 0.5px;
    animation: tsSlideIn 0.3s ease;
    display: flex; align-items: center; gap: 10px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5);
}
#ts-toast.flagged {
    background: rgba(255,51,85,0.12);
    border-color: rgba(255,51,85,0.5);
    color: #ff3355;
}
#ts-toast .ts-close {
    margin-left: auto; cursor: pointer; opacity: 0.6; font-size: 14px;
}
</style>
""", unsafe_allow_html=True)


# ── Session State ───────────────────────────────────────────────────────────────
if "running"              not in st.session_state: st.session_state.running              = False
if "violations"           not in st.session_state: st.session_state.violations           = deque(maxlen=20)
if "prob_history"         not in st.session_state: st.session_state.prob_history         = deque(maxlen=60)
if "session_id"           not in st.session_state: st.session_state.session_id           = f"PRO-{os.urandom(3).hex().upper()}"
if "total_viol"           not in st.session_state: st.session_state.total_viol           = 0
if "prev_mouth_dist"      not in st.session_state: st.session_state.prev_mouth_dist      = 0
if "talking_counter"      not in st.session_state: st.session_state.talking_counter      = 0

# Integrity score state
if "integrity_score"      not in st.session_state: st.session_state.integrity_score      = 100
if "score_log"            not in st.session_state: st.session_state.score_log            = []
if "session_start"        not in st.session_state: st.session_state.session_start        = None
if "violation_timers"     not in st.session_state: st.session_state.violation_timers     = {}
if "active_violations"    not in st.session_state: st.session_state.active_violations    = set()
if "penalized_this_tick"  not in st.session_state: st.session_state.penalized_this_tick  = set()
if "exam_ended"           not in st.session_state: st.session_state.exam_ended           = False
if "final_report"         not in st.session_state: st.session_state.final_report         = None

# Evidence / screenshot state
if "evidence_log"             not in st.session_state: st.session_state.evidence_log             = []
if "screenshot_cooldowns"     not in st.session_state: st.session_state.screenshot_cooldowns     = {}

# Tab / window switching state
init_tab_state()
if "exam_terminated" not in st.session_state: st.session_state.exam_terminated = False

# ── Load ML models ──────────────────────────────────────────────────────────────
models = load_models()


# ════════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════════
hcol1, hcol2 = st.columns([2, 1])
with hcol1:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:14px;padding:8px 0 16px">
      <div style="width:44px;height:44px;background:linear-gradient(135deg,rgba(0,212,255,0.15),rgba(0,255,136,0.08));
                  border:1.5px solid rgba(0,212,255,0.4);border-radius:10px;display:flex;align-items:center;
                  justify-content:center;font-size:20px;box-shadow:0 0 20px rgba(0,212,255,0.15)">🛡</div>
      <div>
        <div style="font-size:18px;font-weight:800;color:#e8f0f5">AI Proctoring System</div>
        <div style="font-size:11px;color:#4a6070;font-family:Space Mono,monospace;letter-spacing:1px">
          Session ID: <span style="color:#00d4ff">{st.session_state.session_id}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with hcol2:
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;padding-top:10px">
      <span class="badge badge-green">● ENGINE CONNECTED</span>
      <span style="font-family:Space Mono,monospace;font-size:13px;color:#e8f0f5;
                   background:#0d1318;border:1px solid #1a2530;padding:6px 14px;
                   border-radius:8px;letter-spacing:2px">
        {datetime.now().strftime("%H:%M:%S")}
      </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  CONTROLS
# ════════════════════════════════════════════════════════════════════
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1, 1, 1, 5])
with ctrl1:
    start = st.button("▶  Start Session" if not st.session_state.running else "⏹  Stop Session")
with ctrl2:
    reset = st.button("↺  Reset")
with ctrl3:
    export = st.button("⬇  Export Log")

if start:
    st.session_state.running = not st.session_state.running
    st.rerun()

if reset:
    st.session_state.running             = False
    st.session_state.violations          = deque(maxlen=20)
    st.session_state.prob_history        = deque(maxlen=60)
    st.session_state.total_viol          = 0
    st.session_state.session_id          = f"PRO-{os.urandom(3).hex().upper()}"
    st.session_state.talking_counter     = 0
    st.session_state.integrity_score     = 100
    st.session_state.score_log           = []
    st.session_state.violation_timers    = {}
    st.session_state.active_violations   = set()
    st.session_state.session_start       = None
    st.session_state.exam_ended          = False
    st.session_state.final_report        = None
    st.session_state.evidence_log            = []
    st.session_state.screenshot_cooldowns    = {}
    reset_tab_state()
    st.session_state.exam_terminated         = False
    st.rerun()

if export and os.path.exists("proctor_log.csv"):
    with open("proctor_log.csv") as f:
        st.download_button("📥 Download CSV", f.read(), "proctor_log.csv", "text/csv")

st.markdown('<hr>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  MAIN LAYOUT — placeholders
# ════════════════════════════════════════════════════════════════════
left_col, right_col = st.columns([1, 2.4], gap="medium")

# ── LEFT COLUMN ──────────────────────────────────────────────────────
with left_col:
    gauge_placeholder = st.empty()
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Integrity Score</div>', unsafe_allow_html=True)
    integrity_placeholder = st.empty()
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)
    breakdown_placeholder = st.empty()
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Active Violations</div>', unsafe_allow_html=True)
    active_violations_placeholder = st.empty()

# ── RIGHT COLUMN ─────────────────────────────────────────────────────
with right_col:
    st.markdown('<div class="section-title">Live Sensors</div>', unsafe_allow_html=True)
    sensor_placeholder = st.empty()
    st.markdown("")

    cam_col, charts_col = st.columns([1.3, 1], gap="medium")
    with cam_col:
        st.markdown('<div class="section-title">Live Camera Feed</div>', unsafe_allow_html=True)
        cam_placeholder = st.empty()
    with charts_col:
        st.markdown('<div class="section-title">Probability Timeline</div>', unsafe_allow_html=True)
        chart_placeholder = st.empty()
        st.markdown('<div class="section-title" style="margin-top:12px">Violation Log</div>', unsafe_allow_html=True)
        log_placeholder = st.empty()

# ── Full-width rows ───────────────────────────────────────────────────
alert_placeholder      = st.empty()
tab_banner_placeholder = st.empty()   # tab-switch warning banner
report_placeholder     = st.empty()

st.markdown('<hr>', unsafe_allow_html=True)

# ── Tab-switch violation log (always visible when session running) ────
st.markdown('<div class="section-title">🔀 Focus Violation Log</div>', unsafe_allow_html=True)
tab_log_placeholder = st.empty()

st.markdown('<hr>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📸 Evidence Captured</div>', unsafe_allow_html=True)
evidence_placeholder = st.empty()

# ── JavaScript Tab / Window Switching Detection ───────────────────────
import streamlit.components.v1 as components

_tab_server_port = 8765  # must match _SERVER_PORT in tab_switch_handler

components.html(f"""
<!DOCTYPE html>
<html>
<head><style>body{{margin:0;overflow:hidden;background:transparent}}</style></head>
<body>
<script>
(function() {{
  const SERVER   = 'http://127.0.0.1:{_tab_server_port}';
  const THROTTLE = 4000;
  let lastSent     = 0;
  let toastTimer   = null;
  let localCount   = 0;
  let sessionActive = false;  // only true when exam session is running

  // ── Poll server for reset + active-session status (every 1.5 s) ─────
  function checkReset() {{
    try {{
      const xhr = new XMLHttpRequest();
      xhr.open('GET', SERVER, true);
      xhr.onload = function() {{
        if (xhr.status === 200) {{
          try {{
            const data = JSON.parse(xhr.responseText);
            sessionActive = !!data.active;
            if (data.reset) {{
              localCount = 0;
              try {{
                const t = window.parent.document.getElementById('ts-toast');
                if (t) t.style.display = 'none';
              }} catch(e) {{}}
            }}
          }} catch(e) {{}}
        }}
      }};
      xhr.send();
    }} catch(e) {{}}
  }}
  setInterval(checkReset, 1500);
  checkReset();  // run immediately on load

  // ── Toast in parent document ─────────────────────────────────────────
  function ensureToast() {{
    const pd = window.parent.document;
    if (pd.getElementById('ts-toast')) return;
    const style = pd.createElement('style');
    style.id = 'ts-toast-styles';
    style.textContent = `
      @keyframes tsSlide {{
        from {{ transform:translateX(-50%) translateY(-18px); opacity:0 }}
        to   {{ transform:translateX(-50%) translateY(0);     opacity:1 }}
      }}
      #ts-toast {{
        display:none;
        position:fixed; top:20px; left:50%; transform:translateX(-50%);
        z-index:2147483647;
        min-width:400px; max-width:580px;
        padding:15px 24px; border-radius:12px;
        font-family:'Space Mono',monospace; font-size:12px; font-weight:700;
        letter-spacing:0.4px; line-height:1.5;
        align-items:center; gap:14px;
        animation:tsSlide 0.3s ease;
        box-shadow:0 8px 36px rgba(0,0,0,0.65);
        transition:opacity 0.45s ease;
      }}
      #ts-toast.ts-warn {{
        background:rgba(255,204,0,0.13);
        border:1.5px solid rgba(255,204,0,0.65);
        color:#ffcc00;
      }}
      #ts-toast.ts-danger {{
        background:rgba(255,51,85,0.13);
        border:1.5px solid rgba(255,51,85,0.65);
        color:#ff3355;
      }}
      #ts-toast-body  {{ flex:1 }}
      #ts-toast-title {{ font-size:13px; margin-bottom:3px }}
      #ts-toast-sub   {{ font-size:10px; opacity:0.75; font-weight:400; letter-spacing:0 }}
      #ts-toast-close {{
        margin-left:auto; cursor:pointer; opacity:0.5;
        font-size:17px; flex-shrink:0; line-height:1;
      }}
      #ts-toast-close:hover {{ opacity:1 }}
    `;
    pd.head.appendChild(style);
    const el = pd.createElement('div');
    el.id = 'ts-toast';
    el.innerHTML =
      '<div id="ts-toast-body">' +
        '<div id="ts-toast-title"></div>' +
        '<div id="ts-toast-sub"></div>' +
      '</div>' +
      '<span id="ts-toast-close">&#x2715;</span>';
    pd.body.appendChild(el);
    pd.getElementById('ts-toast-close').addEventListener('click', () => {{
      pd.getElementById('ts-toast').style.display = 'none';
      if (toastTimer) clearTimeout(toastTimer);
    }});
  }}

  function showToast(count) {{
    try {{
      ensureToast();
      const pd    = window.parent.document;
      const toast = pd.getElementById('ts-toast');
      const title = pd.getElementById('ts-toast-title');
      const sub   = pd.getElementById('ts-toast-sub');
      if (!toast) return;

      let t, s, cls;
      if (count === 1) {{
        t   = '[!] Warning: Tab switching detected';
        s   = 'This action is being monitored. Please stay on the exam tab.';
        cls = 'ts-warn';
      }} else if (count === 2) {{
        t   = '[!!] Second tab switch detected';
        s   = 'One more warning before score deduction begins.';
        cls = 'ts-warn';
      }} else if (count === 3) {{
        t   = '[!!!] Final warning — third tab switch detected';
        s   = 'Next switch will deduct 100 integrity points from your score.';
        cls = 'ts-warn';
      }} else {{
        t   = '[VIOLATION] Tab switch #' + count + ' detected';
        s   = '100 integrity points have been deducted from your score.';
        cls = 'ts-danger';
      }}

      title.textContent   = t;
      sub.textContent     = s;
      toast.className     = cls;
      toast.style.opacity = '1';
      toast.style.display = 'flex';

      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(() => {{
        toast.style.opacity = '0';
        setTimeout(() => {{
          toast.style.display = 'none';
          toast.style.opacity = '1';
        }}, 460);
      }}, 5000);   // 5 seconds visible
    }} catch(e) {{}}
  }}

  // ── POST event to backend ────────────────────────────────────────────
  function sendEvent(type) {{
    if (!sessionActive) return;   // ignore all events before session starts
    const now = Date.now();
    if (now - lastSent < THROTTLE) return;
    lastSent = now;
    localCount++;
    showToast(localCount);

    const payload = {{
      type: type,
      ts:   new Date().toISOString(),
      id:   String(now) + '_' + Math.random().toString(36).slice(2, 8),
    }};

    try {{
      const xhr = new XMLHttpRequest();
      xhr.open('POST', SERVER, true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.send(JSON.stringify(payload));
    }} catch(e) {{}}
  }}

  // ── Attach to PARENT window ──────────────────────────────────────────
  try {{
    const pw = window.parent;
    pw.document.addEventListener('visibilitychange', function() {{
      if (pw.document.visibilityState === 'hidden') sendEvent('tab_switch');
    }});
    pw.addEventListener('blur', function() {{ sendEvent('window_blur'); }});
  }} catch(e) {{
    document.addEventListener('visibilitychange', function() {{
      if (document.visibilityState === 'hidden') sendEvent('tab_switch');
    }});
    window.addEventListener('blur', function() {{ sendEvent('window_blur'); }});
  }}

}})();
</script>
</body>
</html>
""", height=0, scrolling=False)


# ════════════════════════════════════════════════════════════════════
#  MAIN CAMERA LOOP
# ════════════════════════════════════════════════════════════════════
if st.session_state.running:

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        st.error("❌ Cannot open camera. Make sure your webcam is connected.")
        st.session_state.running = False
    else:
        if st.session_state.session_start is None:
            st.session_state.session_start = time.time()
            st.session_state.exam_ended    = False
            st.session_state.final_report  = None
            set_session_active(True)

        pTime = time.time()

        while st.session_state.running:
            ret, frame = cap.read()
            if not ret:
                break

            frame           = cv2.flip(frame, 1)
            annotated, det  = process_frame(frame, models)

            # FPS overlay
            cTime = time.time()
            fps   = 1 / max(cTime - pTime, 0.001)
            pTime = cTime
            cv2.putText(annotated, f"FPS: {int(fps)}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

            susp = det["suspicion"]
            st.session_state.prob_history.append(susp)

            # Store raw frame so capture_evidence can access it from scoring engine
            st.session_state.current_frame = frame.copy()

            # ── Tab / window switching events ─────────────────────────
            process_tab_events(current_frame=frame)

            # ── Integrity scoring ─────────────────────────────────────
            active_viols = update_integrity_score(det)
            iscore       = st.session_state.integrity_score
            sev, _, scol = severity_label(iscore)

            # ── Score zero → terminate exam immediately ────────────────
            if iscore <= 0 or st.session_state.exam_terminated:
                st.session_state.exam_terminated = True
                st.session_state.running         = False
                break

            cv2.putText(
                annotated, f"INTEGRITY: {iscore}", (10, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 255, 136) if iscore >= 80 else (0, 220, 255) if iscore >= 60 else (51, 51, 255),
                1,
            )

            # ── Threat gauge ──────────────────────────────────────────
            gauge_placeholder.markdown(
                f'<div style="background:#0d1318;border:1px solid #1a2530;border-radius:14px;'
                f'padding:20px;text-align:center">'
                f'<div class="section-title" style="margin-bottom:14px">Threat Analysis</div>'
                f'{gauge_svg(susp)}</div>',
                unsafe_allow_html=True,
            )

            # ── Integrity score gauge ─────────────────────────────────
            integrity_placeholder.markdown(
                f'<div style="background:#0d1318;border:1px solid #1a2530;border-radius:14px;'
                f'padding:20px;text-align:center">'
                f'{integrity_score_svg(iscore)}</div>',
                unsafe_allow_html=True,
            )

            # ── Active violations panel ───────────────────────────────
            if active_viols:
                av_items   = ""
                viol_labels = {
                    "multi_face":    ("🧑‍🤝‍🧑", "Multiple Faces",       "#ff3355"),
                    "no_face":       ("❌",       "No Face Detected",    "#ff3355"),
                    "phone":         ("📱",       "Phone Detected",      "#ff3355"),
                    "laptop":        ("💻",       "Laptop Detected",     "#ff6622"),
                    "looking_away":  ("👀",       "Looking Away",        "#ffcc00"),
                    "eye_gaze_away": ("👁",        "Suspicious Gaze",    "#ffcc00"),
                    "talking":       ("🎤",       "Talking",             "#ffcc00"),
                }
                for vk in active_viols:
                    icon_v, lbl_v, col_v = viol_labels.get(vk, ("⚠", vk, "#ffcc00"))
                    penalty_v = PENALTIES.get(vk, 0)
                    av_items += (
                        f'<div style="display:flex;align-items:center;justify-content:space-between;'
                        f'padding:7px 10px;background:rgba({",".join(str(int(col_v.lstrip("#")[i:i+2], 16)) for i in (0,2,4))},0.08);'
                        f'border:1px solid {col_v}44;border-radius:8px;margin-bottom:6px">'
                        f'<span style="font-size:12px">{icon_v} '
                        f'<span style="color:{col_v};font-weight:700">{lbl_v}</span></span>'
                        f'<span style="font-family:Space Mono,monospace;font-size:11px;color:{col_v}">−{penalty_v} pts</span>'
                        f'</div>'
                    )
                active_violations_placeholder.markdown(
                    f'<div style="background:#0d1318;border:1px solid #1a2530;'
                    f'border-radius:10px;padding:12px">{av_items}</div>',
                    unsafe_allow_html=True,
                )
            else:
                active_violations_placeholder.markdown(
                    '<div style="background:#0d1318;border:1px solid rgba(0,255,136,0.2);'
                    'border-radius:10px;padding:12px;text-align:center;'
                    'font-family:Space Mono,monospace;font-size:10px;color:#00ff88;'
                    'letter-spacing:1px">✔ No active violations</div>',
                    unsafe_allow_html=True,
                )

            # ── Score breakdown bars ──────────────────────────────────
            hs  = (5 if det["head_state"] == "warn" else 15) if det["head_state"] in ("warn", "alert") else 0
            es  = 8  if det.get("eye") in {"Looking Left","Looking Right","Looking Up","Looking Down"} else 0
            aus = 20 if det["talking"]               else 0
            ps  = 30 if det["phone"]                 else 0
            ls  = 25 if det.get("laptop", False)     else 0
            fs  = 50 if det["num_faces"] > 1         else 0

            def br(label, val, mx, color):
                pct = int(val / mx * 100)
                return (
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
                    f'<div style="font-size:11px;color:#7a95a5;width:80px;flex-shrink:0">{label}</div>'
                    f'<div style="flex:1;height:6px;background:#1a2530;border-radius:3px;overflow:hidden">'
                    f'<div style="height:100%;width:{pct}%;background:{color};border-radius:3px;transition:width 0.5s"></div>'
                    f'</div>'
                    f'<div style="font-family:Space Mono,monospace;font-size:11px;color:{color};width:25px;text-align:right">{val}</div>'
                    f'</div>'
                )

            breakdown_placeholder.markdown(
                '<div style="background:#0d1318;border:1px solid #1a2530;border-radius:12px;padding:16px">'
                + br("Head Pose",  hs,  20, "#ffcc00" if hs  else "#00ff88")
                + br("Eye Gaze",   es,   8, "#ffcc00" if es  else "#00ff88")
                + br("Audio",      aus, 20, "#ffcc00" if aus else "#00ff88")
                + br("Phone",      ps,  30, "#ff3355" if ps  else "#00ff88")
                + br("Laptop",     ls,  25, "#ff6622" if ls  else "#00ff88")
                + br("Multi-Face", fs,  50, "#ff3355" if fs  else "#00ff88")
                + '</div>',
                unsafe_allow_html=True,
            )

            # ── Sensors ───────────────────────────────────────────────
            _gaze_dir = det.get("eye", "Unknown")
            _gaze_away = _gaze_dir in {"Looking Left","Looking Right","Looking Up","Looking Down"}
            s1 = sensor_html("🧍", "Head Pose",    det["head"],  det["head_state"])
            s2 = sensor_html("👁", "Eye Gaze",     _gaze_dir,    "warn" if _gaze_away else det["eye_state"])
            s3 = sensor_html("🎤", "Audio",
                             "Talking!" if det["talking"] else "Silent",
                             "alert"    if det["talking"] else "ok")
            _env_label = (
                "Phone!"      if det["phone"]
                else "Laptop!"     if det.get("laptop", False)
                else "Multi-Face"  if det["num_faces"] > 1
                else "Secured"
            )
            _env_state = (
                "alert" if (det["phone"] or det.get("laptop", False) or det["num_faces"] > 1)
                else "ok"
            )
            s4 = sensor_html("🖥", "Environment", _env_label, _env_state)

            sensor_placeholder.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">'
                f'{s1}{s2}{s3}{s4}</div>',
                unsafe_allow_html=True,
            )

            # ── Camera feed ───────────────────────────────────────────
            img_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            cam_placeholder.image(img_rgb, channels="RGB", use_container_width=True)

            # ── Probability chart ─────────────────────────────────────
            chart_placeholder.markdown(
                f'<div style="background:#0d1318;border:1px solid #1a2530;border-radius:10px;padding:10px 12px">'
                f'{bar_chart_html(st.session_state.prob_history)}</div>',
                unsafe_allow_html=True,
            )

            # ── Violation log ─────────────────────────────────────────
            items = ""
            for v in list(st.session_state.violations)[:8]:
                dot = "log-dot-r" if v["level"] == "red" else "log-dot-y"
                penalty_tag = (
                    f'<span style="font-family:Space Mono,monospace;font-size:10px;color:#ff3355">−{v["penalty"]}</span>'
                    if v.get("penalty") else ""
                )
                items += (
                    f'<div class="log-item"><div class="{dot}"></div>'
                    f'<div class="log-text">{v["text"]}</div>'
                    f'{penalty_tag}'
                    f'<div class="log-time">{v["time"]}</div></div>'
                )
            if not items:
                items = (
                    '<div style="text-align:center;padding:14px;font-family:Space Mono,monospace;'
                    'font-size:10px;color:#4a6070;letter-spacing:1px">No violations</div>'
                )

            log_placeholder.markdown(
                f'<div style="background:#0d1318;border:1px solid #1a2530;border-radius:10px;'
                f'padding:12px;max-height:200px;overflow-y:auto">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                f'<span style="font-size:13px;font-weight:700">⚑ Violations</span>'
                f'<span style="background:rgba(255,51,85,0.12);border:1px solid rgba(255,51,85,0.3);'
                f'color:#ff3355;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;'
                f'font-family:Space Mono,monospace">{st.session_state.total_viol}</span></div>'
                f'{items}</div>',
                unsafe_allow_html=True,
            )

            # ── Alert banner ──────────────────────────────────────────
            if iscore < 40:
                alert_placeholder.markdown(
                    f'<div class="alert-banner">🚨 HIGH RISK — Integrity: {iscore}/100 — Immediate review required</div>',
                    unsafe_allow_html=True,
                )
            elif iscore < 60:
                alert_placeholder.markdown(
                    f'<div style="padding:12px 20px;border-radius:10px;background:rgba(255,204,0,0.08);'
                    f'border:1px solid rgba(255,204,0,0.35);color:#ffcc00;font-weight:700;font-size:13px;margin-bottom:14px">'
                    f'⚠ SUSPICIOUS — Integrity: {iscore}/100 — Monitoring elevated</div>',
                    unsafe_allow_html=True,
                )
            elif susp >= 30:
                msg = (
                    "🚨 HIGH RISK — Immediate review required"
                    if susp >= 60
                    else "⚠ SUSPICIOUS ACTIVITY — Monitoring elevated"
                )
                alert_placeholder.markdown(
                    f'<div class="alert-banner">{msg}</div>',
                    unsafe_allow_html=True,
                )
            else:
                alert_placeholder.empty()

            # ── Tab-switch warning banner ─────────────────────────────
            tab_banner_placeholder.markdown(
                tab_switch_banner_html(
                    st.session_state.tab_switch_count,
                    st.session_state.tab_switch_flagged,
                ),
                unsafe_allow_html=True,
            )

            # ── Tab-switch log panel ──────────────────────────────────
            tab_log_placeholder.markdown(
                tab_switch_log_html(st.session_state.tab_switch_log),
                unsafe_allow_html=True,
            )

            # ── Evidence panel ────────────────────────────────────────
            evidence_placeholder.markdown(
                evidence_panel_html(st.session_state.evidence_log),
                unsafe_allow_html=True,
            )

            time.sleep(0.03)  # ~30 fps cap

        # ── Session ended — generate final report ─────────────────────
        cap.release()
        set_session_active(False)

        # Finalise any in-progress violation video clips
        from utils.video_recorder import stop_all as stop_all_videos
        stop_all_videos()

        # ── CHEATING DETECTED — Score hit zero ────────────────────────
        if st.session_state.exam_terminated:
            report_placeholder.markdown("""
            <div style="background:#0d1318;border:2px solid rgba(255,51,85,0.6);
                        border-radius:16px;padding:40px;margin-top:20px;text-align:center">
              <div style="font-size:56px;margin-bottom:16px">🚫</div>
              <div style="font-size:22px;font-weight:800;color:#ff3355;
                          letter-spacing:1px;margin-bottom:14px">
                EXAM SESSION TERMINATED
              </div>
              <div style="font-size:14px;color:#7a95a5;max-width:520px;margin:0 auto 24px;
                          line-height:1.8;font-family:Space Mono,monospace">
                Your integrity score has dropped to zero as a result of repeated and
                confirmed violations detected during this session — including unauthorised
                tab switching, focus loss, and other monitored behaviour.<br><br>
                This session has been flagged as a <span style="color:#ff3355;font-weight:700">
                suspected cheating attempt</span> and all evidence, including timestamped
                screenshots and a full violation log, has been recorded and saved.<br><br>
                You cannot continue or restart this exam without administrator review.
              </div>
              <div style="display:inline-flex;align-items:center;gap:10px;
                          background:rgba(255,51,85,0.08);
                          border:1px solid rgba(255,51,85,0.4);
                          border-radius:10px;padding:12px 24px;margin-bottom:28px">
                <span style="font-size:18px">⚠️</span>
                <span style="font-family:Space Mono,monospace;font-size:11px;
                             color:#ff3355;font-weight:700;letter-spacing:1px">
                  INTEGRITY SCORE: 0 / 100 — SESSION LOCKED
                </span>
              </div>
              <div style="font-family:Space Mono,monospace;font-size:10px;
                          color:#4a6070;letter-spacing:1px">
                Press the  ↺ Reset  button above to clear this session and start fresh.
              </div>
            </div>
            """, unsafe_allow_html=True)
            # Lock everything else — skip the normal report
            st.stop()

        if not st.session_state.exam_terminated and not st.session_state.exam_ended:
            st.session_state.exam_ended = True
            report   = generate_final_report()
            rc_color = {"Safe": "#00ff88", "Suspicious": "#ffcc00", "Cheating": "#ff3355"}.get(
                report["risk_class"], "#7a95a5"
            )
            vsum_rows = "".join(
                f'<tr>'
                f'<td style="padding:6px 10px;color:#7a95a5">{vt}</td>'
                f'<td style="padding:6px 10px;font-family:Space Mono,monospace;color:#e8f0f5;text-align:center">{vd["count"]}</td>'
                f'<td style="padding:6px 10px;font-family:Space Mono,monospace;color:#ff3355;text-align:center">−{vd["total_penalty"]}</td>'
                f'</tr>'
                for vt, vd in report["violation_summary"].items()
            ) or (
                '<tr><td colspan="3" style="padding:10px;text-align:center;color:#4a6070">'
                'No violations recorded</td></tr>'
            )

            report_placeholder.markdown(f"""
            <div style="background:#0d1318;border:1px solid #1a2530;border-radius:14px;padding:24px;margin-top:16px">
              <div style="font-size:15px;font-weight:800;margin-bottom:16px;color:#e8f0f5">
                📋 Exam Integrity Report — {report['session_id']}
              </div>
              <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px">
                <div style="background:#080c10;border:1px solid #1a2530;border-radius:10px;padding:14px;text-align:center">
                  <div style="font-size:10px;letter-spacing:2px;color:#4a6070;margin-bottom:6px;font-family:Space Mono,monospace">FINAL SCORE</div>
                  <div style="font-size:28px;font-weight:800;color:{rc_color};font-family:Space Mono,monospace">{report['final_score']}</div>
                  <div style="font-size:10px;color:#4a6070;font-family:Space Mono,monospace">/100</div>
                </div>
                <div style="background:#080c10;border:1px solid #1a2530;border-radius:10px;padding:14px;text-align:center">
                  <div style="font-size:10px;letter-spacing:2px;color:#4a6070;margin-bottom:6px;font-family:Space Mono,monospace">RISK CLASS</div>
                  <div style="font-size:18px;font-weight:800;color:{rc_color}">{report['risk_class']}</div>
                </div>
                <div style="background:#080c10;border:1px solid #1a2530;border-radius:10px;padding:14px;text-align:center">
                  <div style="font-size:10px;letter-spacing:2px;color:#4a6070;margin-bottom:6px;font-family:Space Mono,monospace">VIOLATIONS</div>
                  <div style="font-size:28px;font-weight:800;color:#e8f0f5;font-family:Space Mono,monospace">{report['total_violations']}</div>
                </div>
                <div style="background:#080c10;border:1px solid #1a2530;border-radius:10px;padding:14px;text-align:center">
                  <div style="font-size:10px;letter-spacing:2px;color:#4a6070;margin-bottom:6px;font-family:Space Mono,monospace">TAB SWITCHES</div>
                  <div style="font-size:28px;font-weight:800;color:#ffcc00;font-family:Space Mono,monospace">{st.session_state.tab_switch_count}</div>
                </div>
              </div>
              <table style="width:100%;border-collapse:collapse;font-size:12px">
                <thead>
                  <tr style="border-bottom:1px solid #1a2530">
                    <th style="padding:6px 10px;text-align:left;color:#4a6070;font-weight:700;letter-spacing:1px;font-size:10px">VIOLATION TYPE</th>
                    <th style="padding:6px 10px;text-align:center;color:#4a6070;font-weight:700;letter-spacing:1px;font-size:10px">COUNT</th>
                    <th style="padding:6px 10px;text-align:center;color:#4a6070;font-weight:700;letter-spacing:1px;font-size:10px">POINTS DEDUCTED</th>
                  </tr>
                </thead>
                <tbody>{vsum_rows}</tbody>
              </table>
            </div>
            """, unsafe_allow_html=True)

else:
    # ── Idle state ────────────────────────────────────────────────────
    # If exam was terminated due to score=0, show the cheating screen
    if st.session_state.get("exam_terminated", False):
        report_placeholder.markdown("""
        <div style="background:#0d1318;border:2px solid rgba(255,51,85,0.6);
                    border-radius:16px;padding:40px;margin-top:20px;text-align:center">
          <div style="font-size:56px;margin-bottom:16px">🚫</div>
          <div style="font-size:22px;font-weight:800;color:#ff3355;
                      letter-spacing:1px;margin-bottom:14px">
            EXAM SESSION TERMINATED
          </div>
          <div style="font-size:14px;color:#7a95a5;max-width:520px;margin:0 auto 24px;
                      line-height:1.8;font-family:Space Mono,monospace">
            Your integrity score has dropped to zero as a result of repeated and
            confirmed violations detected during this session — including unauthorised
            tab switching, focus loss, and other monitored behaviour.<br><br>
            This session has been flagged as a <span style="color:#ff3355;font-weight:700">
            suspected cheating attempt</span> and all evidence, including timestamped
            screenshots and a full violation log, has been recorded and saved.<br><br>
            You cannot continue or restart this exam without administrator review.
          </div>
          <div style="display:inline-flex;align-items:center;gap:10px;
                      background:rgba(255,51,85,0.08);
                      border:1px solid rgba(255,51,85,0.4);
                      border-radius:10px;padding:12px 24px;margin-bottom:28px">
            <span style="font-size:18px">⚠️</span>
            <span style="font-family:Space Mono,monospace;font-size:11px;
                         color:#ff3355;font-weight:700;letter-spacing:1px">
              INTEGRITY SCORE: 0 / 100 — SESSION LOCKED
            </span>
          </div>
          <div style="font-family:Space Mono,monospace;font-size:10px;
                      color:#4a6070;letter-spacing:1px">
            Press the  ↺ Reset  button above to clear this session and start fresh.
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    gauge_placeholder.markdown(
        f'<div style="background:#0d1318;border:1px solid #1a2530;border-radius:14px;padding:20px;text-align:center">'
        f'<div class="section-title" style="margin-bottom:14px">Threat Analysis</div>'
        f'{gauge_svg(0)}</div>',
        unsafe_allow_html=True,
    )

    integrity_placeholder.markdown(
        f'<div style="background:#0d1318;border:1px solid #1a2530;border-radius:14px;padding:20px;text-align:center">'
        f'{integrity_score_svg(st.session_state.integrity_score)}</div>',
        unsafe_allow_html=True,
    )

    active_violations_placeholder.markdown(
        '<div style="background:#0d1318;border:1px solid rgba(0,255,136,0.2);border-radius:10px;padding:12px;'
        'text-align:center;font-family:Space Mono,monospace;font-size:10px;color:#00ff88;letter-spacing:1px">'
        '✔ No active violations</div>',
        unsafe_allow_html=True,
    )

    breakdown_placeholder.markdown(
        '<div style="background:#0d1318;border:1px solid #1a2530;border-radius:12px;padding:16px;'
        'text-align:center;font-family:Space Mono,monospace;font-size:11px;color:#4a6070;letter-spacing:1px">'
        'Start session to see breakdown</div>',
        unsafe_allow_html=True,
    )

    sensor_placeholder.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">'
        f'{sensor_html("🧍","Head Pose","Unknown","none")}'
        f'{sensor_html("👁","Eye Direction","Unknown","none")}'
        f'{sensor_html("🎤","Audio","Silent","ok")}'
        f'{sensor_html("🖥","Environment","Secured","ok")}'
        f'</div>',
        unsafe_allow_html=True,
    )

    cam_placeholder.markdown(
        '<div style="background:#050a0e;border:1px solid #1a2530;border-radius:10px;'
        'aspect-ratio:16/9;display:flex;flex-direction:column;align-items:center;'
        'justify-content:center;gap:8px">'
        '<div style="font-size:40px;opacity:0.2">🎥</div>'
        '<div style="font-size:13px;color:#4a6070;font-weight:600">Camera feed inactive</div>'
        '<div style="font-size:11px;color:#1a2530;font-family:Space Mono,monospace">'
        'Click ▶ Start Session to begin</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    chart_placeholder.markdown(
        f'<div style="background:#0d1318;border:1px solid #1a2530;border-radius:10px;padding:10px 12px">'
        f'{bar_chart_html([])}</div>',
        unsafe_allow_html=True,
    )

    log_placeholder.markdown(
        '<div style="background:#0d1318;border:1px solid #1a2530;border-radius:10px;padding:12px">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
        '<span style="font-size:13px;font-weight:700">⚑ Violations</span>'
        '<span style="background:rgba(255,51,85,0.12);border:1px solid rgba(255,51,85,0.3);color:#ff3355;'
        'font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;'
        'font-family:Space Mono,monospace">0</span></div>'
        '<div style="text-align:center;padding:14px;font-family:Space Mono,monospace;'
        'font-size:10px;color:#4a6070;letter-spacing:1px">No violations</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    evidence_placeholder.markdown(
        evidence_panel_html(st.session_state.evidence_log),
        unsafe_allow_html=True,
    )

    tab_banner_placeholder.markdown(
        tab_switch_banner_html(
            st.session_state.tab_switch_count,
            st.session_state.tab_switch_flagged,
        ),
        unsafe_allow_html=True,
    )

    tab_log_placeholder.markdown(
        tab_switch_log_html(st.session_state.tab_switch_log),
        unsafe_allow_html=True,
    )