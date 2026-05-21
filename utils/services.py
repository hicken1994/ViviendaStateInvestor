import pandas as pd
from utils.connection import get_conn_ro
from utils.cache import cached


def get_dashboard_kpis() -> dict:
    with get_conn_ro() as conn:
        df_main = pd.read_sql("""
            SELECT
                COUNT(*)                                          AS total_props,
                ROUND(AVG(opportunity_score), 2)                  AS avg_score,
                ROUND(AVG(precio_total), 0)                       AS avg_price,
                ROUND(AVG(
                    (precio_m2_barrio * metros - precio_total)
                    / NULLIF(precio_total, 0) * 100
                ), 2)                                             AS avg_rent
            FROM vista_oportunidades_ai
        """, conn)

        df_opp = pd.read_sql("""
            SELECT COUNT(*) AS oportunidades
            FROM vista_oportunidades_ai
            WHERE opportunity_score >= 70
        """, conn)

        df_events = pd.read_sql("""
            SELECT COUNT(*) AS recent_events
            FROM events
            WHERE timestamp >= datetime('now', '-7 days')
        """, conn)

    return {
        "total_props":   int(df_main["total_props"].iloc[0]),
        "avg_score":     float(df_main["avg_score"].iloc[0]),
        "oportunidades": int(df_opp["oportunidades"].iloc[0]),
        "avg_price":     float(df_main["avg_price"].iloc[0]),
        "avg_rent":      float(df_main["avg_rent"].iloc[0]),
        "recent_events": int(df_events["recent_events"].iloc[0]),
    }


def get_decision_distribution() -> pd.DataFrame:
    with get_conn_ro() as conn:
        return pd.read_sql("""
            SELECT
                CASE
                    WHEN opportunity_score >= 70 THEN 'COMPRAR'
                    WHEN opportunity_score >= 50 THEN 'NEGOCIAR'
                    ELSE 'DESCARTAR'
                END AS decision,
                COUNT(*) AS count
            FROM vista_oportunidades_ai
            GROUP BY decision
            ORDER BY count DESC
        """, conn)


def get_score_distribution() -> pd.DataFrame:
    with get_conn_ro() as conn:
        return pd.read_sql(
            "SELECT opportunity_score FROM vista_oportunidades_ai", conn
        )


def get_top_barrios(limit: int = 10) -> pd.DataFrame:
    with get_conn_ro() as conn:
        df = pd.read_sql(
            "SELECT * FROM radar_oportunidades ORDER BY opportunity_index DESC", conn
        )
    return df.head(limit)


@cached(ttl=30)
def get_dashboard_events(limit: int = 5) -> pd.DataFrame:
    with get_conn_ro() as conn:
        return pd.read_sql("""
            SELECT property_id, event_type, old_value, new_value, timestamp
            FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        """, conn, params=(limit,))


@cached(ttl=300)
def get_map_data() -> pd.DataFrame:
    with get_conn_ro() as conn:
        return pd.read_sql("""
            SELECT distrito, latitud, longitud
            FROM mapas_distritos
        """, conn)


@cached(ttl=300)
def get_distrito_mapping() -> pd.DataFrame:
    with get_conn_ro() as conn:
        return pd.read_sql("SELECT * FROM distrito_mapping", conn)


@cached(ttl=300)
def get_barrios() -> pd.DataFrame:
    with get_conn_ro() as conn:
        return pd.read_sql("""
            SELECT *
            FROM radar_oportunidades
            ORDER BY opportunity_index DESC
        """, conn)


@cached(ttl=60)
def get_barrio_rent(barrio: str, default: float = 20) -> float:
    with get_conn_ro() as conn:
        df = pd.read_sql(
            "SELECT precio_m2_alquiler FROM barrio_rent WHERE barrio = ?",
            conn, params=(barrio,)
        )
    if not df.empty:
        return float(df["precio_m2_alquiler"].iloc[0])
    return default


@cached(ttl=30)
def get_top_opportunities(limit: int = 50) -> pd.DataFrame:
    with get_conn_ro() as conn:
        return pd.read_sql("""
            SELECT *
            FROM vista_oportunidades_ai
            ORDER BY opportunity_score DESC
            LIMIT ?
        """, conn, params=(limit,))
