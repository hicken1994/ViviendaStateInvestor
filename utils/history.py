import hashlib
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def _seed_from_id(prop_id) -> int:
    h = hashlib.md5(str(prop_id).encode()).hexdigest()
    return int(h[:8], 16)


def generate_price_history(
    prop_id,
    current_price: float,
    days: int = 60,
    volatility: float = 0.015,
) -> pd.DataFrame:
    """Genera historico sintetico de precios para una propiedad.

    Usa el property_id como seed para que sea deterministico.
    Simula un random walk alrededor del precio actual.
    """
    rng = random.Random(_seed_from_id(prop_id))
    np_rng = np.random.default_rng(_seed_from_id(prop_id))

    returns = np_rng.normal(0, volatility, days)
    # Hacer que el precio actual sea el ultimo punto
    price_series = [current_price]
    for ret in reversed(returns):
        prev = price_series[0]
        price_series.insert(0, prev / (1 + ret))

    dates = [datetime.now() - timedelta(days=days - i) for i in range(days + 1)]

    return pd.DataFrame({
        "fecha": dates,
        "precio": [round(p, 2) for p in price_series],
    })


def compute_price_trend(history: pd.DataFrame) -> dict:
    """Calcula tendencia del historico de precios."""
    if history.empty or len(history) < 2:
        return {"trend": "estable", "change_pct": 0, "min": 0, "max": 0}

    first = history["precio"].iloc[0]
    last = history["precio"].iloc[-1]
    change_pct = round((last - first) / first * 100, 2)

    if change_pct > 3:
        trend = "subiendo"
    elif change_pct < -3:
        trend = "bajando"
    else:
        trend = "estable"

    return {
        "trend": trend,
        "change_pct": change_pct,
        "min": round(history["precio"].min(), 2),
        "max": round(history["precio"].max(), 2),
        "avg": round(history["precio"].mean(), 2),
    }


def get_or_generate_history(prop_id, current_price: float, days: int = 60) -> pd.DataFrame:
    """Intenta leer historico de la DB, si no existe genera uno sintetico."""
    import logging
    from utils.connection import get_conn_ro

    try:
        with get_conn_ro() as conn:
            df = pd.read_sql(
                "SELECT precio_total as precio, fecha FROM property_history "
                "WHERE property_id = ? ORDER BY fecha ASC",
                conn, params=(str(prop_id),),
            )
            if len(df) >= 5:
                return df
    except Exception as e:
        logging.getLogger(__name__).warning(
            "No se pudo leer historico para %s: %s", prop_id, e
        )

    return generate_price_history(prop_id, current_price, days)
