# ── ui/gauges.py — SVG circular gauge components ──────────────────────────────

from engine.scoring_engine import severity_label


def gauge_svg(pct: int) -> str:
    """
    Render a circular SVG gauge showing threat-probability percentage.

    Args:
        pct: Integer 0–100 representing suspicion level.

    Returns:
        str: HTML/SVG string ready for st.markdown(unsafe_allow_html=True).
    """
    r     = 70
    circ  = 2 * 3.14159 * r
    offset = circ - (pct / 100) * circ
    color  = "#00ff88" if pct < 25 else "#ffcc00" if pct < 60 else "#ff3355"
    label  = "LOW RISK"    if pct < 25 else "MEDIUM RISK" if pct < 60 else "HIGH RISK"
    icon   = "🛡"           if pct < 25 else "⚠"          if pct < 60 else "🚨"
    badge_cls = "badge-green" if pct < 25 else "badge-yellow" if pct < 60 else "badge-red"

    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:12px;">
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle cx="80" cy="80" r="{r}" fill="none" stroke="#1a2530" stroke-width="10"/>
        <circle cx="80" cy="80" r="{r}" fill="none" stroke="{color}" stroke-width="10"
          stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"
          stroke-linecap="round"
          transform="rotate(-90 80 80)"
          style="filter:drop-shadow(0 0 8px {color});transition:stroke-dashoffset 0.8s ease"/>
        <text x="80" y="74" text-anchor="middle" fill="{color}"
          style="font-family:Space Mono,monospace;font-size:26px;font-weight:700">{pct}%</text>
        <text x="80" y="94" text-anchor="middle" fill="#4a6070"
          style="font-family:Space Mono,monospace;font-size:9px;letter-spacing:2px">PROBABILITY</text>
      </svg>
      <div style="text-align:center;">
        <div style="font-size:9px;letter-spacing:2px;color:#4a6070;margin-bottom:6px;
                    font-family:Space Mono,monospace">CURRENT RISK</div>
        <span class="badge {badge_cls}">{icon} {label}</span>
      </div>
    </div>
    """


def integrity_score_svg(score: int) -> str:
    """
    Render a circular SVG gauge showing the integrity score (100 = perfect).

    Args:
        score: Integer 0–100.

    Returns:
        str: HTML/SVG string ready for st.markdown(unsafe_allow_html=True).
    """
    r          = 70
    circ       = 2 * 3.14159 * r
    pct        = max(0, min(100, score))
    offset     = circ * (1 - pct / 100)
    sev, badge_cls, color = severity_label(score)
    icon = "🛡" if score >= 80 else "⚠" if score >= 60 else "⚡" if score >= 40 else "🚨"

    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:12px;">
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle cx="80" cy="80" r="{r}" fill="none" stroke="#1a2530" stroke-width="10"/>
        <circle cx="80" cy="80" r="{r}" fill="none" stroke="{color}" stroke-width="10"
          stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"
          stroke-linecap="round"
          transform="rotate(-90 80 80)"
          style="filter:drop-shadow(0 0 8px {color});transition:stroke-dashoffset 0.6s ease"/>
        <text x="80" y="70" text-anchor="middle" fill="{color}"
          style="font-family:Space Mono,monospace;font-size:26px;font-weight:700">{pct}</text>
        <text x="80" y="88" text-anchor="middle" fill="#7a95a5"
          style="font-family:Space Mono,monospace;font-size:9px;letter-spacing:2px">INTEGRITY</text>
        <text x="80" y="103" text-anchor="middle" fill="#4a6070"
          style="font-family:Space Mono,monospace;font-size:8px;letter-spacing:1px">/ 100</text>
      </svg>
      <div style="text-align:center;">
        <div style="font-size:9px;letter-spacing:2px;color:#4a6070;margin-bottom:6px;
                    font-family:Space Mono,monospace">EXAM INTEGRITY</div>
        <span class="badge {badge_cls}">{icon} {sev.upper()}</span>
      </div>
    </div>
    """
