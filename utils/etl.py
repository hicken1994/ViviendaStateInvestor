"""
ETL: Carga datos reales desde Idealista18 + Kaggle a Supabase.
Correr una sola vez para poblar la base de datos.

Usage:
    python -m utils.etl                    # solo transforma local
    python -m utils.etl --supabase         # transforma + sube a Supabase
"""

import argparse, bz2, logging, os, re, sys, tempfile
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

DATA_DIR = Path("data_raw")
DATA_DIR.mkdir(exist_ok=True)

# ── Fuentes ──────────────────────────────────────────────────

IDEALISTA18_URL = (
    "https://raw.githubusercontent.com/paezha/idealista18/"
    "master/data/Madrid_Sale.rda"
)
KAGGLE_DATASET = "kanchana1990/madrid-idealista-property-listings"

# ── Mapeo distritos Madrid (normalizacion) ────────────────────

DISTRITOS_MADRID = [
    "centro", "arganzuela", "retiro", "salamanca", "chamartin",
    "tetuan", "chamberi", "fuencarral-el pardo", "moncloa-aravaca",
    "latina", "carabanchel", "usera", "puente de vallecas",
    "moratalaz", "ciudad lineal", "hortaleza", "villaverde",
    "villa de vallecas", "vicalvaro", "san blas-canillejas", "barajas",
]

# ── Descarga ──────────────────────────────────────────────────

def _download_file(url: str, dest: Path):
    import urllib.request
    log.info("  descargando %s ...", url.split("/")[-1])
    urllib.request.urlretrieve(url, dest)
    log.info("  -> %s (%.0f KB)", dest.name, dest.stat().st_size / 1024)


def download_all():
    log.info("=== Descargando datasets ===")
    rda_path = DATA_DIR / "Madrid_Sale.rda"
    if not rda_path.exists():
        _download_file(IDEALISTA18_URL, rda_path)
    else:
        log.info("  %s ya existe, skip", rda_path.name)

    try:
        import kagglehub
        path = kagglehub.dataset_download(KAGGLE_DATASET)
        for f in os.listdir(path):
            dest = DATA_DIR / f
            if not dest.exists():
                import shutil
                shutil.copy2(os.path.join(path, f), dest)
                log.info("  copiado %s (%.0f KB)", f, dest.stat().st_size / 1024)
    except Exception as e:
        log.warning("  Kaggle download fallo: %s", e)


# ── Lectura ───────────────────────────────────────────────────

def read_idealista18() -> pd.DataFrame:
    log.info("=== Leyendo Idealista18 ===")
    rda_path = DATA_DIR / "Madrid_Sale.rda"
    if not rda_path.exists():
        download_all()

    import rdata
    with open(rda_path, "rb") as f:
        decomp = bz2.decompress(f.read())
    with tempfile.NamedTemporaryFile(suffix=".RData", delete=False) as tmp:
        tmp.write(decomp)
        tmp_name = tmp.name
    parsed = rdata.read_rda(tmp_name)
    os.unlink(tmp_name)
    df = parsed["Madrid_Sale"]
    log.info("  leidas %d filas x %d cols", df.shape[0], df.shape[1])
    return df


def read_kaggle() -> pd.DataFrame:
    log.info("=== Leyendo Kaggle ===")
    csv_path = DATA_DIR / "idealista_madrid.csv"
    if not csv_path.exists():
        download_all()
    df = pd.read_csv(csv_path)
    log.info("  leidas %d filas x %d cols", df.shape[0], df.shape[1])
    return df


# ── Extraer distrito desde direccion ─────────────────────────

def _extract_barrio(address: str) -> str:
    if not isinstance(address, str):
        return None
    addr_lower = address.lower()
    for d in DISTRITOS_MADRID:
        if d in addr_lower:
            return d
    return None


# ── Transform ─────────────────────────────────────────────────

def transform_idealista18(raw: pd.DataFrame) -> pd.DataFrame:
    log.info("=== Transformando Idealista18 ===")

    df = raw.copy()

    # Filtrar solo Madrid ciudad (coordenadas dentro de M-30 aprox)
    df = df[
        df["LONGITUDE"].between(-3.78, -3.58) &
        df["LATITUDE"].between(40.35, 40.50)
    ].copy()
    log.info("  filas en Madrid: %d", len(df))

    # Columnas core
    result = pd.DataFrame()
    result["propiedad_id"] = range(1, len(df) + 1)
    result["precio_total"] = df["PRICE"].astype(float)
    result["metros"] = df["CONSTRUCTEDAREA"].astype(float)
    result["precio_m2"] = df["UNITPRICE"].astype(float)
    result["rooms"] = pd.to_numeric(df["ROOMNUMBER"], errors="coerce").astype("Int64")
    result["bathrooms"] = pd.to_numeric(df["BATHNUMBER"], errors="coerce").astype("Int64")
    result["has_lift"] = pd.to_numeric(df["HASLIFT"], errors="coerce").astype("Int64")
    result["has_terrace"] = pd.to_numeric(df["HASTERRACE"], errors="coerce").astype("Int64")
    result["construction_year"] = df["CONSTRUCTIONYEAR"].astype("Int64")
    result["latitude"] = df["LATITUDE"].astype(float)
    result["longitude"] = df["LONGITUDE"].astype(float)

    # precio_m2_barrio: promedio por barrio (calculado despues de asignar barrio)
    # Primero asignamos barrio dummy hasta tener geo-asignacion
    result["barrio"] = _assign_barrio_geo(df)

    # precio_m2_barrio = media del precio_m2 por barrio
    barrio_avg = result.groupby("barrio")["precio_m2"].transform("mean")
    result["precio_m2_barrio"] = barrio_avg.round(1)

    # diferencia_pct = (barrio - prop) / barrio * 100
    result["diferencia_pct"] = (
        (result["precio_m2_barrio"] - result["precio_m2"])
        / result["precio_m2_barrio"].replace(0, np.nan) * 100
    ).round(2)

    # opportunity_score heuristico basado en descuento + metros
    desc_norm = result["diferencia_pct"].clip(-5, 35)
    result["opportunity_score"] = (
        30 + desc_norm * 1.5
        + result["metros"].clip(40, 200) / 200 * 10
    ).clip(0, 99).round(1)

    # Segun perfil: score_* como NULL (se computan en runtime)
    result["score_descuento"] = None
    result["score_precio"] = None
    result["score_liquidez"] = None
    result["score_tamano"] = None
    result["rentabilidad_estimada"] = result["diferencia_pct"].round(2)
    result["decision"] = None
    result["is_premium"] = (result["opportunity_score"] > 80).astype(int)
    result["source"] = "idealista18"
    result["source_id"] = df["ASSETID"].astype(str)

    # Limpiar filas sin barrio
    before = len(result)
    result = result[result["barrio"].notna()].copy()
    log.info("  descartadas %d sin barrio", before - len(result))
    log.info("  total transformadas: %d", len(result))

    return result


def _assign_barrio_geo(df: pd.DataFrame) -> pd.Series:
    """Asigna distrito basado en coordenadas (aproximacion rough)."""
    # Usamos las coordenadas de mapas_distritos como centroides
    coord_map = {
        "centro": (40.4189, -3.7038),
        "arganzuela": (40.3989, -3.6994),
        "retiro": (40.4132, -3.6831),
        "salamanca": (40.4298, -3.6800),
        "chamartin": (40.4556, -3.6800),
        "tetuan": (40.4607, -3.6975),
        "chamberi": (40.4358, -3.7045),
        "fuencarral-el pardo": (40.4867, -3.7267),
        "moncloa-aravaca": (40.4353, -3.7264),
        "latina": (40.4036, -3.7467),
        "carabanchel": (40.3900, -3.7400),
        "usera": (40.3886, -3.7028),
        "puente de vallecas": (40.3956, -3.6683),
        "moratalaz": (40.4114, -3.6492),
        "ciudad lineal": (40.4456, -3.6511),
        "hortaleza": (40.4733, -3.6436),
        "villaverde": (40.3489, -3.7089),
        "villa de vallecas": (40.3806, -3.6208),
        "vicalvaro": (40.4033, -3.6081),
        "san blas-canillejas": (40.4392, -3.6158),
        "barajas": (40.4735, -3.5777),
    }

    lats = df["LATITUDE"].values
    lons = df["LONGITUDE"].values
    result = []
    for lat, lon in zip(lats, lons):
        best_dist = float("inf")
        best_barrio = None
        for barrio, (blat, blon) in coord_map.items():
            d = (lat - blat) ** 2 + (lon - blon) ** 2
            if d < best_dist:
                best_dist = d
                best_barrio = barrio
        result.append(best_barrio)
    return pd.Series(result, index=df.index)


def transform_kaggle(raw: pd.DataFrame) -> pd.DataFrame:
    log.info("=== Transformando Kaggle ===")
    df = raw.copy()

    result = pd.DataFrame()
    result["propiedad_id"] = range(1, len(df) + 1)
    result["precio_total"] = pd.to_numeric(df["price"], errors="coerce")
    result["metros"] = pd.to_numeric(df["sqft"], errors="coerce")
    result["precio_m2"] = (result["precio_total"] / result["metros"]).round(1)
    result["rooms"] = pd.to_numeric(df["rooms"], errors="coerce").fillna(0).astype(int)
    result["bathrooms"] = pd.to_numeric(df["baths"], errors="coerce").fillna(0).astype(int)
    result["has_lift"] = 0
    result["has_terrace"] = 0
    result["construction_year"] = pd.NA
    result["latitude"] = None
    result["longitude"] = None

    # Extraer barrio desde address
    result["barrio"] = df["address"].apply(_extract_barrio)

    # precio_m2_barrio
    barrio_avg = result.groupby("barrio")["precio_m2"].transform("mean")
    result["precio_m2_barrio"] = barrio_avg.round(1)

    result["diferencia_pct"] = (
        (result["precio_m2_barrio"] - result["precio_m2"])
        / result["precio_m2_barrio"].replace(0, np.nan) * 100
    ).round(2)

    desc_norm = result["diferencia_pct"].clip(-5, 35)
    result["opportunity_score"] = (
        30 + desc_norm * 1.5
        + result["metros"].clip(40, 200) / 200 * 10
    ).clip(0, 99).round(1)

    result["score_descuento"] = None
    result["score_precio"] = None
    result["score_liquidez"] = None
    result["score_tamano"] = None
    result["rentabilidad_estimada"] = result["diferencia_pct"].round(2)
    result["decision"] = None
    result["is_premium"] = (result["opportunity_score"] > 80).astype(int)
    result["source"] = "kaggle"
    result["source_id"] = df["id"].astype(str)

    # Filtrar nulos criticos
    before = len(result)
    result = result.dropna(subset=["precio_total", "metros", "barrio"])
    log.info("  descartadas %d sin datos criticos", before - len(result))
    log.info("  total transformadas: %d", len(result))

    return result


# ── Computar tablas auxiliares ────────────────────────────────

def build_barrio_rent(oportunidades: pd.DataFrame) -> pd.DataFrame:
    rent_map = {
        "centro": 28, "arganzuela": 22, "retiro": 26, "salamanca": 28,
        "chamartin": 24, "tetuan": 20, "chamberi": 26,
        "fuencarral-el pardo": 18, "moncloa-aravaca": 22,
        "latina": 16, "carabanchel": 15, "usera": 14,
        "puente de vallecas": 14, "moratalaz": 16, "ciudad lineal": 18,
        "hortaleza": 18, "villaverde": 12, "villa de vallecas": 14,
        "vicalvaro": 14, "san blas-canillejas": 16, "barajas": 18,
    }
    rows = []
    for barrio in oportunidades["barrio"].unique():
        rent = rent_map.get(str(barrio).lower(), 15)
        rows.append({"barrio": barrio, "precio_m2_alquiler": rent})
    return pd.DataFrame(rows)


def build_radar(oportunidades: pd.DataFrame) -> pd.DataFrame:
    radar = (
        oportunidades
        .groupby("barrio")
        .agg(
            oportunidades=("propiedad_id", "count"),
            descuento_medio=("diferencia_pct", "mean"),
            precio_m2_medio=("precio_m2", "mean"),
            opportunity_index=("opportunity_score", "mean"),
        )
        .reset_index()
    )
    radar.columns = ["barrio", "oportunidades", "descuento_medio",
                     "precio_m2_medio", "opportunity_index"]
    radar["descuento_medio"] = radar["descuento_medio"].round(2)
    radar["precio_m2_medio"] = radar["precio_m2_medio"].round(2)
    radar["opportunity_index"] = radar["opportunity_index"].round(2)
    return radar


def build_distrito_mapping() -> pd.DataFrame:
    mapping = [
        ("centro", "centro"), ("arganzuela", "arganzuela"),
        ("retiro", "retiro"), ("salamanca", "salamanca"),
        ("chamartin", "chamartin"), ("tetuan", "tetuan"),
        ("chamberi", "chamberi"),
        ("fuencarral-el pardo", "fuencarral-el pardo"),
        ("moncloa-aravaca", "moncloa-aravaca"),
        ("latina", "latina"), ("carabanchel", "carabanchel"),
        ("usera", "usera"),
        ("puente de vallecas", "puente de vallecas"),
        ("moratalaz", "moratalaz"), ("ciudad lineal", "ciudad lineal"),
        ("hortaleza", "hortaleza"), ("villaverde", "villaverde"),
        ("villa de vallecas", "villa de vallecas"),
        ("vicalvaro", "vicalvaro"),
        ("san blas-canillejas", "san blas-canillejas"),
        ("barajas", "barajas"),
    ]
    return pd.DataFrame(mapping, columns=["distrito_raw", "distrito_mapa"])


def build_mapas_distritos() -> pd.DataFrame:
    coords = [
        ("centro", 40.4189, -3.7038), ("arganzuela", 40.3989, -3.6994),
        ("retiro", 40.4132, -3.6831), ("salamanca", 40.4298, -3.6800),
        ("chamartin", 40.4556, -3.6800), ("tetuan", 40.4607, -3.6975),
        ("chamberi", 40.4358, -3.7045),
        ("fuencarral-el pardo", 40.4867, -3.7267),
        ("moncloa-aravaca", 40.4353, -3.7264),
        ("latina", 40.4036, -3.7467), ("carabanchel", 40.3900, -3.7400),
        ("usera", 40.3886, -3.7028),
        ("puente de vallecas", 40.3956, -3.6683),
        ("moratalaz", 40.4114, -3.6492), ("ciudad lineal", 40.4456, -3.6511),
        ("hortaleza", 40.4733, -3.6436), ("villaverde", 40.3489, -3.7089),
        ("villa de vallecas", 40.3806, -3.6208),
        ("vicalvaro", 40.4033, -3.6081),
        ("san blas-canillejas", 40.4392, -3.6158),
        ("barajas", 40.4735, -3.5777),
    ]
    return pd.DataFrame(coords, columns=["distrito", "latitud", "longitud"])


# ── Export ────────────────────────────────────────────────────

def save_parquet(op: pd.DataFrame, prefix: str = "oportunidades"):
    path = DATA_DIR / f"{prefix}_transformado.parquet"
    op.to_parquet(path, index=False)
    log.info("  guardado: %s (%.0f KB)", path.name, path.stat().st_size / 1024)


# ── Supabase upsert ──────────────────────────────────────────

def _get_supabase():
    import re
    with open(".streamlit/secrets.toml") as f:
        content = f.read()
    url = re.search(r'SUPABASE_URL\s*=\s*"([^"]+)"', content).group(1)
    key = re.search(r'SUPABASE_SERVICE_ROLE_KEY\s*=\s*"([^"]+)"', content).group(1)
    from supabase import create_client
    return create_client(url, key)


def _upsert_table(sb, table: str, df: pd.DataFrame, batch_size: int = 500):
    """Upsert en lotes via REST API."""
    total = len(df)
    log.info("  subiendo %d filas a %s (lotes de %d)...", total, table, batch_size)

    # Convertir NaN/NaT a None para JSON, e Int64/float64-like a int limpio
    df_clean = df.copy()

    # Columnas que en Supabase son INTEGER pero llegan como float
    int_cols = ["rooms", "bathrooms", "has_lift", "has_terrace",
                "is_premium", "construction_year", "propiedad_id"]
    for col in int_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").astype("Int64")

    # Int64 → object con None para NA
    for col in df_clean.select_dtypes(include=["Int64", "Int32"]).columns:
        df_clean[col] = df_clean[col].astype(object).where(df_clean[col].notna(), None)

    # Reemplazar NaN/NaT/Inf en columnas float
    for col in df_clean.select_dtypes(include=["float64", "float32"]).columns:
        df_clean[col] = df_clean[col].where(df_clean[col].notna() & np.isfinite(df_clean[col]), None)

    records = df_clean.to_dict(orient="records")
    ok = 0
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        try:
            sb.table(table).upsert(batch).execute()
            ok += len(batch)
        except Exception as e:
            log.warning("  error lote %d-%d: %s", i, i + len(batch), e)
        if (i // batch_size) % 5 == 0 and i > 0:
            log.info("  ... %d / %d", ok, total)
    log.info("  completado: %d / %d filas en %s", ok, total, table)
    return ok


def upload_all(op, barrio_rent, radar, distrito_mapping, mapas):
    log.info("=== Subiendo a Supabase ===")
    sb = _get_supabase()

    _upsert_table(sb, "oportunidades", op, batch_size=300)
    _upsert_table(sb, "barrio_rent", barrio_rent, batch_size=100)
    _upsert_table(sb, "radar_oportunidades", radar, batch_size=100)
    _upsert_table(sb, "distrito_mapping", distrito_mapping, batch_size=100)
    _upsert_table(sb, "mapas_distritos", mapas, batch_size=100)

    log.info("=== TODO SUBIDO A SUPABASE ===")


# ── Main ──────────────────────────────────────────────────────

def run(use_supabase: bool = False):
    download_all()

    op_list = []
    try:
        raw_i18 = read_idealista18()
        op_i18 = transform_idealista18(raw_i18)
        op_list.append(op_i18)
        log.info("Idealista18: %d propiedades transformadas", len(op_i18))
    except Exception as e:
        log.warning("Idealista18 fallo: %s", e)

    try:
        raw_k = read_kaggle()
        op_k = transform_kaggle(raw_k)
        op_list.append(op_k)
        log.info("Kaggle: %d propiedades transformadas", len(op_k))
    except Exception as e:
        log.warning("Kaggle fallo: %s", e)

    if not op_list:
        log.error("No se pudo transformar ninguna fuente")
        return

    op = pd.concat(op_list, ignore_index=True)
    op["propiedad_id"] = range(1, len(op) + 1)
    log.info("Total combinado: %d propiedades", len(op))

    save_parquet(op)

    barrio_rent = build_barrio_rent(op)
    radar = build_radar(op)
    distrito_mapping = build_distrito_mapping()
    mapas = build_mapas_distritos()

    log.info("Tablas auxiliares: barrio_rent=%d, radar=%d, mapping=%d, mapas=%d",
             len(barrio_rent), len(radar), len(distrito_mapping), len(mapas))

    if use_supabase:
        upload_all(op, barrio_rent, radar, distrito_mapping, mapas)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--supabase", action="store_true",
                        help="Subir los datos transformados a Supabase")
    args = parser.parse_args()
    run(use_supabase=args.supabase)
