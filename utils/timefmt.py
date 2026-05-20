from datetime import datetime
import re


def parse_timestamp(ts) -> datetime | None:
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def time_ago(ts) -> str:
    """Formatea un timestamp a texto relativo en espanol."""
    dt = parse_timestamp(ts)
    if dt is None:
        return "fecha desconocida"

    now = datetime.now()
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 0:
        return "en el futuro"

    intervals = [
        (31536000, "ano"),
        (2592000, "mes"),
        (604800, "semana"),
        (86400, "dia"),
        (3600, "hora"),
        (60, "minuto"),
    ]

    for divisor, unit in intervals:
        count = seconds // divisor
        if count >= 2:
            plural = unit + ("s" if unit not in ("mes") else "es")
            return f"hace {count} {plural}"
        elif count == 1:
            return f"hace 1 {unit}"

    return "hace instantes"


def format_timestamp(ts) -> str:
    """Formatea un timestamp para mostrar: fecha + hora relativa."""
    dt = parse_timestamp(ts)
    if dt is None:
        return "—"
    return f"{dt.strftime('%d/%m/%Y %H:%M')} ({time_ago(ts)})"
