from utils.connection import get_conn_ro

DATASET_VERSION = "2.2"
DATASET_DATE = "Mayo 2026"
DATASET_YEAR = 2018  # Año real de los datos de Idealista18

FUENTES = {
    "ine": {
        "nombre": "INE — Instituto Nacional de Estadística",
        "descripcion": "Datos demográficos, población por distrito y tendencias del mercado de vivienda.",
        "url": "https://www.ine.es",
    },
    "ministerio": {
        "nombre": "Ministerio de Transportes, Movilidad y Agenda Urbana",
        "descripcion": "Índices de precios de vivienda, estadísticas de compra-venta y precios de alquiler por zonas.",
        "url": "https://www.mitma.gob.es",
    },
    "idealista": {
        "nombre": "Idealista — Portal Inmobiliario (API en tiempo real)",
        "descripcion": "Datos de oferta en vivo del mercado de Madrid vía API. Los suscriptores Pro y Enterprise acceden a datos actualizados diariamente.",
        "url": "https://www.idealista.com",
        "api": True,
    },
    "idealista_synthetic": {
        "nombre": "Dataset sintético de Madrid",
        "descripcion": "3.000+ propiedades simuladas con patrones realistas del mercado de Madrid. Usado por el plan Starter.",
        "url": None,
        "api": False,
    },
    "fotocasa": {
        "nombre": "Fotocasa — Portal Inmobiliario",
        "descripcion": "Datos de referencia cruzada para validación de tendencias de precios por barrio.",
        "url": "https://www.fotocasa.es",
    },
}

METODOLOGIA = """
**Vivienda AI** procesa datos del mercado inmobiliario de Madrid combinando múltiples fuentes oficiales y portales inmobiliarios.

### Planes de datos
- **Starter** (gratis): Dataset sintético con **más de 3.000 propiedades** simuladas con patrones realistas del mercado de Madrid.
- **Pro y Enterprise**: Datos en vivo de Idealista vía API, actualizados diariamente con propiedades reales del mercado.

El dataset contiene más de 30 atributos por propiedad que incluyen precio, superficie, ubicación, y scores de inversión calculados mediante un modelo
multifactorial.

### Score de inversión (0–100)
El score total se calcula ponderando 5 dimensiones, cada una con un peso ajustable según tu perfil de inversor:

| Dimensión | Máximo | Qué mide |
|-----------|--------|----------|
| **Descuento** | 40 pts | Diferencia entre precio de venta y valor de mercado del barrio |
| **Precio vs Barrio** | 25 pts | Ratio precio/m² de la propiedad vs media del barrio |
| **Liquidez** | 15 pts | Facilidad para alquilar según el tamaño (50–90 m² puntúa más) |
| **Tamaño** | 10 pts | Metros cuadrados útiles (más de 60 m² puntúa más) |
| **Ruido** | 10 pts | Nivel de ruido estimado de la zona |

Los pesos se ajustan por perfil: un perfil **Básico** pondera más liquidez y ruido (seguridad),
mientras que un perfil **Avanzado** pondera más descuento y precio (rentabilidad).

### Rentabilidad estimada
Se calcula como: `(valor_mercado - precio_compra) / precio_compra * 100`
donde `valor_mercado` es el precio medio por m² del barrio multiplicado por los metros de la propiedad.

### Decisiones de inversión
- **COMPRAR**: Score alto y rentabilidad por encima del umbral del perfil
- **NEGOCIAR**: Score aceptable pero margen ajustado — conviene negociar el precio
- **DESCARTAR**: Los números no alcanzan los mínimos del perfil
"""

DISCLAIMER = """
> ⚠️ **Aviso importante**: Esta herramienta es un demostrador educativo. Los datos mostrados
> son simulaciones basadas en información pública (plan Starter) o datos en vivo de Idealista (Pro/Enterprise)
> y no constituyen asesoramiento financiero. Toda decisión de inversión debe ser validada con profesionales
> del sector inmobiliario.
"""


def get_last_event_timestamp() -> str | None:
    import pandas as pd
    with get_conn_ro() as conn:
        df = pd.read_sql("SELECT timestamp FROM events ORDER BY timestamp DESC LIMIT 1", conn)
    if not df.empty:
        return str(df["timestamp"].iloc[0])
    return None


def _detect_data_source() -> str:
    import pandas as pd
    with get_conn_ro() as conn:
        df = pd.read_sql("SELECT DISTINCT source FROM oportunidades WHERE source IS NOT NULL LIMIT 1", conn)
    if not df.empty:
        src = str(df["source"].iloc[0])
        return {"idealista18": f"Idealista18 ({DATASET_YEAR})", "kaggle": f"Kaggle + Idealista18 ({DATASET_YEAR})"}.get(src, src.capitalize())
    return "Dataset sintético"


def get_dataset_stats(user_plan: str = "Starter") -> dict:
    import pandas as pd
    if user_plan in ("Pro", "Enterprise") and _idealista_available():
        return {
            "propiedades": 9999,
            "barrios": 21,
            "distritos": 21,
            "eventos": 0,
            "fuente": "Idealista API (tiempo real)",
        }
    with get_conn_ro() as conn:
        total = pd.read_sql("SELECT COUNT(*) as c FROM oportunidades", conn)["c"].iloc[0]
        barrios = pd.read_sql("SELECT DISTINCT barrio FROM oportunidades", conn).shape[0]
        distritos = pd.read_sql("SELECT COUNT(*) as c FROM mapas_distritos", conn)["c"].iloc[0]
        eventos = pd.read_sql("SELECT COUNT(*) as c FROM events", conn)["c"].iloc[0]
    return {
        "propiedades": int(total),
        "barrios": int(barrios),
        "distritos": int(distritos),
        "eventos": int(eventos),
        "fuente": _detect_data_source(),
    }


def _idealista_available():
    try:
        from utils.idealista import is_configured
        return is_configured()
    except ImportError:
        return False
