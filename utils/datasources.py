from datetime import datetime

DATASET_VERSION = "2.1"
DATASET_DATE = "Mayo 2026"

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
        "nombre": "Idealista — Portal Inmobiliario",
        "descripcion": "Precios de oferta actuales del mercado de Madrid, filtrados y procesados para análisis de inversión.",
        "url": "https://www.idealista.com",
    },
    "fotocasa": {
        "nombre": "Fotocasa — Portal Inmobiliario",
        "descripcion": "Datos de referencia cruzada para validación de tendencias de precios por barrio.",
        "url": "https://www.fotocasa.es",
    },
}

METODOLOGIA = f"""
**Vivienda AI** procesa datos del mercado inmobiliario de Madrid combinando múltiples fuentes oficiales y portales inmobiliarios.
El dataset contiene **más de 3.000 propiedades** distribuidas en los **21 distritos** de Madrid, con más de 30 atributos
por propiedad que incluyen precio, superficie, ubicación, y scores de inversión calculados mediante un modelo
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
> son simulaciones basadas en información pública y no constituyen asesoramiento financiero.
> Toda decisión de inversión debe ser validada con profesionales del sector inmobiliario.
"""


def get_last_event_timestamp() -> str | None:
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect("real_estate.db")
    try:
        df = pd.read_sql("SELECT timestamp FROM events ORDER BY timestamp DESC LIMIT 1", conn)
        if not df.empty:
            return str(df["timestamp"].iloc[0])
    finally:
        conn.close()
    return None


def get_dataset_stats() -> dict:
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect("real_estate.db")
    try:
        total = pd.read_sql("SELECT COUNT(*) as c FROM vista_oportunidades_ai", conn)["c"].iloc[0]
        barrios = pd.read_sql("SELECT COUNT(DISTINCT barrio) as c FROM vista_oportunidades_ai", conn)["c"].iloc[0]
        distritos = pd.read_sql("SELECT COUNT(*) as c FROM mapas_distritos", conn)["c"].iloc[0]
        eventos = pd.read_sql("SELECT COUNT(*) as c FROM events", conn)["c"].iloc[0]
    finally:
        conn.close()
    return {
        "propiedades": int(total),
        "barrios": int(barrios),
        "distritos": int(distritos),
        "eventos": int(eventos),
    }
