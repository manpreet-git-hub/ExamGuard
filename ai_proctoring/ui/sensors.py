# ── ui/sensors.py — Live sensor card HTML component ───────────────────────────


def sensor_html(icon: str, label: str, value: str, state: str) -> str:
    """
    Render a single sensor card as an HTML string.

    Args:
        icon:   Emoji / character shown at top-left of the card.
        label:  Short descriptor shown below the icon (e.g. "Head Pose").
        value:  Current reading displayed prominently (e.g. "Looking Left").
        state:  One of "ok" | "warn" | "alert" | "none" — controls colour theme.

    Returns:
        str: HTML string for one sensor card.
    """
    card_cls = {
        "ok":    "sensor-card-active",
        "warn":  "sensor-card-warn",
        "alert": "sensor-card-alert",
    }.get(state, "")

    val_cls = {
        "ok":    "sensor-value-c",
        "warn":  "sensor-value-y",
        "alert": "sensor-value-r",
        "none":  "sensor-value-m",
    }.get(state, "sensor-value-m")

    dot_color = {
        "ok":    "#00d4ff",
        "warn":  "#ffcc00",
        "alert": "#ff3355",
        "none":  "#1a2530",
    }.get(state, "#1a2530")

    return f"""
    <div class="sensor-card {card_cls}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <span style="font-size:18px;opacity:0.7">{icon}</span>
        <div style="width:8px;height:8px;border-radius:50%;background:{dot_color};
                    box-shadow:0 0 8px {dot_color}"></div>
      </div>
      <div class="sensor-label">{label}</div>
      <div class="{val_cls}">{value}</div>
    </div>"""
