# ── ui/charts.py — Probability timeline bar chart ─────────────────────────────


def bar_chart_html(history) -> str:
    """
    Render a compact HTML bar chart of suspicion-probability history.

    Args:
        history: Iterable of int values (0–100) ordered oldest → newest.

    Returns:
        str: HTML string suitable for st.markdown(unsafe_allow_html=True).
    """
    if not history:
        return (
            '<div style="height:120px;display:flex;align-items:center;'
            'justify-content:center;font-family:Space Mono,monospace;'
            'font-size:11px;color:#4a6070;letter-spacing:1px">'
            'Awaiting historical data...</div>'
        )

    bars = ""
    for v in list(history)[-50:]:
        h = max(4, int(v / 100 * 110))
        c = "#00ff88" if v < 25 else "#ffcc00" if v < 60 else "#ff3355"
        bars += (
            f'<div style="flex:1;height:{h}px;background:{c};'
            f'border-radius:2px 2px 0 0;min-width:3px;box-shadow:0 0 4px {c}88"></div>'
        )

    return (
        f'<div style="display:flex;align-items:flex-end;gap:2px;'
        f'height:120px;padding:6px 4px 0">{bars}</div>'
    )
