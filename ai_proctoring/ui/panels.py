# ── ui/panels.py — Compound UI panel HTML components ──────────────────────────

from config import EVIDENCE_DIR, TAB_SWITCH_THRESHOLD


# ── Tab-switch warning banner ──────────────────────────────────────────────────

def tab_switch_banner_html(count: int, flagged: bool) -> str:
    """
    Render a dismissible-style warning banner for tab/window violations.

    Args:
        count:   Total tab-switch violations so far.
        flagged: True when the threshold has been exceeded.

    Returns:
        str: HTML string, or empty string if no violations yet.
    """
    if count == 0:
        return ""

    remaining = max(0, TAB_SWITCH_THRESHOLD - count)

    if flagged:
        color   = "#ff3355"
        bg      = "rgba(255,51,85,0.08)"
        border  = "rgba(255,51,85,0.35)"
        icon    = "🚨"
        title   = "EXAM FLAGGED — Repeated tab switching detected"
        sub     = f"This session has been flagged for review. Total focus violations: {count}"
    elif count >= TAB_SWITCH_THRESHOLD - 1:
        color   = "#ff3355"
        bg      = "rgba(255,51,85,0.06)"
        border  = "rgba(255,51,85,0.3)"
        icon    = "⚠"
        title   = f"Warning: Tab switching detected ({count} time{'s' if count>1 else ''})"
        sub     = "One more violation will flag this exam session."
    else:
        color   = "#ffcc00"
        bg      = "rgba(255,204,0,0.06)"
        border  = "rgba(255,204,0,0.3)"
        icon    = "👁"
        title   = f"Warning: Tab switching detected ({count} time{'s' if count>1 else ''})"
        sub     = f"This action is monitored. {remaining} more violation{'s' if remaining>1 else ''} before session is flagged."

    return (
        f'<div style="padding:12px 18px;border-radius:10px;background:{bg};'
        f'border:1px solid {border};margin-bottom:12px;'
        f'display:flex;align-items:flex-start;gap:12px">'
        f'  <span style="font-size:18px;flex-shrink:0">{icon}</span>'
        f'  <div>'
        f'    <div style="font-weight:700;font-size:13px;color:{color};margin-bottom:3px">{title}</div>'
        f'    <div style="font-size:11px;color:#7a95a5;font-family:Space Mono,monospace">{sub}</div>'
        f'  </div>'
        f'</div>'
    )


def tab_switch_log_html(tab_log: list) -> str:
    """
    Render the tab-switch violation log as a compact HTML panel.

    Args:
        tab_log: List of dicts from st.session_state.tab_switch_log.

    Returns:
        str: HTML string ready for st.markdown(unsafe_allow_html=True).
    """
    if not tab_log:
        return (
            '<div style="background:#0d1318;border:1px solid #1a2530;border-radius:10px;'
            'padding:14px;text-align:center;font-family:Space Mono,monospace;'
            'font-size:10px;color:#4a6070;letter-spacing:1px">No focus violations</div>'
        )

    rows = ""
    for rec in reversed(tab_log[-8:]):
        vtype = rec.get("vtype", "tab_switch")
        icon  = "🔀" if vtype == "tab_switch" else "🪟"
        color = "#ffcc00"
        rows += (
            f'<div style="display:flex;align-items:center;gap:8px;padding:6px 8px;'
            f'background:rgba(255,204,0,0.04);border:1px solid rgba(255,204,0,0.15);'
            f'border-radius:7px;margin-bottom:5px;font-size:11px">'
            f'  <span style="font-size:13px">{icon}</span>'
            f'  <span style="color:#7a95a5;flex:1;font-family:Space Mono,monospace">{rec["label"]}</span>'
            f'  <span style="color:#ff3355;font-family:Space Mono,monospace;font-size:10px">−{rec["penalty"]}</span>'
            f'  <span style="color:#4a6070;font-family:Space Mono,monospace;font-size:10px">{rec["ts"]}</span>'
            f'</div>'
        )

    count = len(tab_log)
    return (
        f'<div style="background:#0d1318;border:1px solid rgba(255,204,0,0.2);'
        f'border-radius:10px;padding:12px">'
        f'  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
        f'    <span style="font-size:12px;font-weight:700;color:#e8f0f5">🔀 Focus Violations</span>'
        f'    <span style="background:rgba(255,204,0,0.12);border:1px solid rgba(255,204,0,0.3);'
        f'      color:#ffcc00;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;'
        f'      font-family:Space Mono,monospace">{count}</span>'
        f'  </div>'
        f'  {rows}'
        f'</div>'
    )




# ── Evidence panel ─────────────────────────────────────────────────────────────

_VTYPE_ICON = {
    "multi_face":        "🧑‍🤝‍🧑",
    "no_face":           "❌",
    "phone":             "📱",
    "laptop":            "💻",
    "looking_away":      "👀",
    "eye_gaze_away":     "👁",
    "talking":           "🎤",
    "identity_mismatch": "🪪",
    "tab_switch":        "🔀",
    "window_blur":       "🪟",
}
_VTYPE_COLOR = {
    "multi_face":        "#ff3355",
    "no_face":           "#ff3355",
    "phone":             "#ff3355",
    "laptop":            "#ff6622",
    "looking_away":      "#ffcc00",
    "eye_gaze_away":     "#ffcc00",
    "talking":           "#ffcc00",
    "identity_mismatch": "#ff3355",
    "tab_switch":        "#ffcc00",
    "window_blur":       "#ffcc00",
}


def evidence_panel_html(evidence_log: list) -> str:
    """
    Render the Evidence Captured section as styled HTML cards.
    Entries may be video clips (media=="video") or legacy screenshots.

    Args:
        evidence_log: List of evidence record dicts from st.session_state.

    Returns:
        str: HTML string ready for st.markdown(unsafe_allow_html=True).
    """
    if not evidence_log:
        return (
            '<div style="background:#0d1318;border:1px solid #1a2530;border-radius:10px;'
            'padding:20px;text-align:center;font-family:Space Mono,monospace;'
            'font-size:11px;color:#4a6070;letter-spacing:1px">'
            '📂 No evidence recorded yet</div>'
        )

    recent = list(reversed(evidence_log))[:6]
    cards  = ""
    for rec in recent:
        vt      = rec["vtype"]
        icon    = _VTYPE_ICON.get(vt, "⚠")
        color   = _VTYPE_COLOR.get(vt, "#ffcc00")
        fname   = rec["filename"]
        is_vid  = rec.get("media") == "video"
        # Media badge
        media_badge = (
            f'<span style="background:rgba(0,212,255,0.12);border:1px solid rgba(0,212,255,0.3);'
            f'color:#00d4ff;font-size:9px;font-weight:700;padding:1px 6px;border-radius:10px;'
            f'font-family:Space Mono,monospace;margin-left:4px">🎥 VIDEO</span>'
            if is_vid else
            f'<span style="background:rgba(120,120,120,0.12);border:1px solid rgba(120,120,120,0.3);'
            f'color:#7a95a5;font-size:9px;font-weight:700;padding:1px 6px;border-radius:10px;'
            f'font-family:Space Mono,monospace;margin-left:4px">📸 IMG</span>'
        )
        dur_tag = ""
        if is_vid and rec.get("duration"):
            dur_tag = (
                f'<div style="font-family:Space Mono,monospace;font-size:10px;color:#00d4ff">'
                f'Duration: {rec["duration"]}s</div>'
            )
        cards += (
            f'<div style="background:#080c10;border:1px solid {color}44;border-radius:10px;'
            f'padding:12px 14px;display:flex;flex-direction:column;gap:4px;min-width:0">'
            f'  <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;flex-wrap:wrap">'
            f'    <span style="font-size:16px">{icon}</span>'
            f'    <span style="color:{color};font-weight:700;font-size:12px">{rec["label"]}</span>'
            f'    {media_badge}'
            f'  </div>'
            f'  <div style="font-family:Space Mono,monospace;font-size:10px;color:#4a6070">{rec["ts"]}</div>'
            f'  {dur_tag}'
            f'  <div style="font-family:Space Mono,monospace;font-size:9px;color:#1a2530;'
            f'       white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{fname}">{fname}</div>'
            f'  <div style="font-family:Space Mono,monospace;font-size:10px;color:#7a95a5">'
            f'    Integrity: <span style="color:{color}">{rec["score"]}</span>/100</div>'
            f'</div>'
        )

    vid_count  = sum(1 for r in evidence_log if r.get("media") == "video")
    total      = len(evidence_log)
    return (
        f'<div style="background:#0d1318;border:1px solid #1a2530;border-radius:12px;padding:14px">'
        f'  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">'
        f'    <span style="font-size:12px;font-weight:700;color:#e8f0f5">🎥 Violation Evidence</span>'
        f'    <div style="display:flex;gap:8px;align-items:center">'
        f'      <span style="font-family:Space Mono,monospace;font-size:10px;color:#00d4ff">{vid_count} clips</span>'
        f'      <span style="background:rgba(255,51,85,0.12);border:1px solid rgba(255,51,85,0.3);'
        f'        color:#ff3355;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;'
        f'        font-family:Space Mono,monospace">{total} total</span>'
        f'    </div>'
        f'  </div>'
        f'  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px">'
        f'    {cards}'
        f'  </div>'
        f'  <div style="margin-top:10px;font-family:Space Mono,monospace;font-size:9px;color:#1a2530;'
        f'       letter-spacing:1px">Saved to: ./{EVIDENCE_DIR}/</div>'
        f'</div>'
    )
