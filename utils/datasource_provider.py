import logging
import pandas as pd
from utils.connection import get_conn_ro
from utils.profiles import compute_score_with_profile, get_perfil
from utils.images import add_images

logger = logging.getLogger(__name__)


def get_properties_for_user(
    user_plan: str,
    limit: int = 100,
) -> pd.DataFrame:
    if user_plan in ("Pro", "Enterprise") and _idealista_available():
        return _get_idealista_properties(limit=min(limit, 200))
    return _get_synthetic_properties(limit=limit)


def _idealista_available() -> bool:
    from utils.idealista import is_configured
    return is_configured()


def _get_synthetic_properties(limit: int = 100) -> pd.DataFrame:
    with get_conn_ro() as conn:
        df = pd.read_sql(
            "SELECT * FROM vista_oportunidades_ai ORDER BY opportunity_score DESC LIMIT ?",
            conn,
            params=(limit,),
        )
    return df


def _get_idealista_properties(limit: int = 100) -> pd.DataFrame:
    try:
        from utils.idealista import bulk_search_madrid

        props = bulk_search_madrid(operation="sale", total_desired=limit)
        if not props:
            logger.warning("Idealista returned no properties, falling back to synthetic")
            return _get_synthetic_properties(limit=limit)

        df = pd.DataFrame(props)
        df = add_images(df)

        perfil = get_perfil("intermedio")
        profile_metrics = df.apply(
            lambda row: compute_score_with_profile(row, perfil),
            axis=1,
            result_type="expand",
        )
        for col in profile_metrics.columns:
            df[col] = profile_metrics[col]

        df = df.sort_values("score_total", ascending=False).reset_index(drop=True)
        return df
    except Exception as e:
        logger.error("Idealista fetch failed: %s — falling back to synthetic", e)
        return _get_synthetic_properties(limit=limit)


def get_total_property_count(user_plan: str) -> int:
    if user_plan in ("Pro", "Enterprise") and _idealista_available():
        return _get_idealista_count()
    return _get_synthetic_count()


def _get_synthetic_count() -> int:
    with get_conn_ro() as conn:
        row = conn.execute("SELECT COUNT(*) FROM vista_oportunidades_ai").fetchone()
        return row[0] if row else 0


def _get_idealista_count() -> int:
    try:
        from utils.idealista import property_search

        result = property_search(max_items=1, num_page=1)
        return result.get("total", 3000)
    except Exception:
        return _get_synthetic_count()


def get_all_barrios(user_plan: str) -> list[str]:
    if user_plan in ("Pro", "Enterprise") and _idealista_available():
        return _get_idealista_barrios()
    return _get_synthetic_barrios()


def _get_synthetic_barrios() -> list[str]:
    with get_conn_ro() as conn:
        rows = conn.execute(
            "SELECT DISTINCT barrio FROM vista_oportunidades_ai ORDER BY barrio"
        ).fetchall()
        return [r[0] for r in rows]


def _get_idealista_barrios() -> list[str]:
    from utils.idealista import FALLBACK_BARRIOS_MADRID
    return FALLBACK_BARRIOS_MADRID
