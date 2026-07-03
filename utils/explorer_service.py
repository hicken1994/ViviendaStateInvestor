import pandas as pd
from utils.connection import get_conn_ro
from utils.train_model import load_model

FEATURE_COLS = [
    "score_descuento", "score_precio", "score_liquidez",
    "score_tamano",
    "precio_total", "metros", "precio_m2", "rentabilidad_estimada",
]


def _build_query(filters: dict) -> tuple[str, list]:
    conditions = []
    params = []

    if filters.get("barrio") and filters["barrio"] != "Todos":
        conditions.append("barrio = ?")
        params.append(filters["barrio"])

    if filters.get("precio_min") is not None:
        conditions.append("precio_total >= ?")
        params.append(filters["precio_min"])
    if filters.get("precio_max") is not None:
        conditions.append("precio_total <= ?")
        params.append(filters["precio_max"])

    if filters.get("score_min") is not None:
        conditions.append("opportunity_score >= ?")
        params.append(filters["score_min"])
    if filters.get("score_max") is not None:
        conditions.append("opportunity_score <= ?")
        params.append(filters["score_max"])

    if filters.get("metros_min") is not None:
        conditions.append("metros >= ?")
        params.append(filters["metros_min"])

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    return where, params


def count_properties(filters: dict) -> int:
    where, params = _build_query(filters)
    with get_conn_ro() as conn:
        df = pd.read_sql(f"SELECT COUNT(*) as total FROM oportunidades {where}", conn, params=params)
    return int(df["total"].iloc[0])


def get_barrios() -> list[str]:
    with get_conn_ro() as conn:
        df = pd.read_sql("SELECT DISTINCT barrio FROM oportunidades ORDER BY barrio", conn)
    return df["barrio"].tolist()


def get_page(filters: dict, offset: int = 0, limit: int = 100) -> pd.DataFrame:
    where, params = _build_query(filters)
    with get_conn_ro() as conn:
        df = pd.read_sql(
            f"""
            SELECT propiedad_id, barrio, metros, precio_total, precio_m2,
                   precio_m2_barrio, opportunity_score,
                   score_descuento, score_precio, score_liquidez, score_tamano,
                   rentabilidad_estimada
            FROM oportunidades {where}
            ORDER BY opportunity_score DESC
            LIMIT ? OFFSET ?
            """,
            conn, params=params + [limit, offset],
        )
    return df


def predict_page(df: pd.DataFrame) -> list[str]:
    clf, _ = load_model()
    if clf is None:
        return []
    X = df[FEATURE_COLS].copy()
    for col in X.select_dtypes(include="object").columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    X = X.fillna(0)
    y_pred = clf.predict(X)
    reverse_map = {0: "DESCARTAR", 1: "NEGOCIAR", 2: "COMPRAR"}
    return [reverse_map.get(v, "?") for v in y_pred]
