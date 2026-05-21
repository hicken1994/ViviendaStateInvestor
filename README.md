# 🏠 Vivienda AI — Madrid Investment Intelligence

**Plataforma interactiva de análisis de inversión inmobiliaria** para el mercado de Madrid. Construida con Streamlit, combina datos simulados del mercado con un sistema de scoring multifactorial para ayudarte a identificar, comparar y vigilar oportunidades de inversión.

## ✨ Funcionalidades

| Funcionalidad | Descripción |
|---|---|
| **📊 Dashboard global** | KPIs del mercado, distribución de scores, top barrios por oportunidad y feed de eventos recientes |
| **📡 Radar de inversión** | Lista priorizada de propiedades con scoring según tu perfil. Incluye simulación de mercado y comparación lateral |
| **🗺️ Mapa de concentración** | Mapa térmico (HeatmapLayer) con PyDeck para visualizar zonas calientes de inversión en Madrid |
| **🏠 Análisis detallado** | Simulación completa de compra: hipoteca, reforma, alquiler, cashflow, ROI y recomendación personalizada |
| **🤖 AI Copilot** | Dos modos: análisis de mercado con scatter plots y análisis individual de propiedades con precio objetivo |
| **⚖️ Comparador** | Compara 2+ propiedades lado a lado con radar overlay, tabla detallada y simulación simultánea |
| **🚨 Alertas + Watchlist** | Feed de eventos del mercado (price drops, yield ups, flash drops) con watchlist de propiedades y barrios |
| **🔥 Flash Drops** | Ofertas temporales con descuento agresivo y expiración visible |

## 🧠 Sistema de Scoring

Cada propiedad recibe una puntuación de **0 a 100** basada en 5 dimensiones ponderadas según tu perfil de inversor:

| Dimensión | Máximo | Descripción |
|---|---|---|
| **Descuento** | 40 pts | Diferencia entre precio de venta y valor de mercado del barrio |
| **Precio vs Barrio** | 25 pts | Ratio precio/m² de la propiedad vs media del barrio |
| **Liquidez** | 15 pts | Facilidad para alquilar según el tamaño (50–90 m² puntúa más) |
| **Tamaño** | 10 pts | Metros cuadrados útiles (más de 60 m² puntúa más) |
| **Ruido** | 10 pts | Nivel de ruido estimado de la zona |

Tres perfiles ajustan los pesos y umbrales:

- **🟢 Básico** — Prioriza seguridad y cashflow positivo. Peso extra en liquidez y ruido
- **🟡 Intermedio** — Equilibrio entre rentabilidad y riesgo
- **🔴 Avanzado** — Máxima rentabilidad. Peso extra en descuento y precio

## 🏛️ Arquitectura

```
vivienda-ai/
├── app.py                    # Dashboard global + sidebar + navegación
├── pages/
│   ├── 1_Radar.py            # Radar de oportunidades con scoring por perfil
│   ├── 2_Mapa.py             # Mapa térmico con PyDeck
│   ├── 3_propiedad.py        # Análisis detallado + simulación de inversión
│   ├── 4_Analisis_Detallado.py  # AI Copilot (mercado / propiedad)
│   ├── 5_Comparador.py       # Comparador lado a lado
│   └── 6_Alertas.py          # Alertas + watchlist
├── utils/
│   ├── services.py           # Capa de acceso a datos (consultas SQL tipadas)
│   ├── db.py                 # Operaciones de escritura, simulación y esquema
│   ├── profiles.py           # Estrategia de perfiles de inversión
│   ├── scoring.py            # Cálculo de scores (delega a profiles)
│   ├── history.py            # Generación sintética de histórico de precios
│   ├── datasources.py        # Fuentes de datos y metadatos del dataset
│   ├── charts.py             # Gráficos Plotly (radar, sparkline, comparador)
│   ├── timefmt.py            # Formateo relativo de timestamps
│   ├── images.py             # Imágenes deterministas por barrio
│   └── tooltips.py           # Tooltips centralizados para toda la UI
├── components/
│   ├── cards.py              # Tarjeta de propiedad reutilizable
│   ├── footer.py             # Footer con fuentes, versión y disclaimer
│   └── score_help.py         # Explicación visual del desglose de scoring
├── dataset_viviendas_madrid_3000.csv  # Dataset simulado
├── real_estate.db            # Base de datos SQLite
└── requirements.txt          # Dependencias
```

## 🚀 Cómo ejecutar

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/vivienda-ai.git
cd vivienda-ai

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la app
streamlit run app.py
```

## 📊 Dataset

El dataset contiene **más de 3.000 propiedades** distribuidas en **21 distritos** de Madrid, generadas sintéticamente con:

- Precios por m² variables por barrio (2.500–7.000 €/m²)
- Superficies entre 40 y 150 m²
- Scores de oportunidad, descuento, rentabilidad y ruido
- Coordenadas geográficas para visualización en mapa

Los precios de alquiler por barrio están precargados en la base de datos.

## 📡 Fuentes de datos de referencia

- **INE** — Instituto Nacional de Estadística
- **Ministerio de Transportes, Movilidad y Agenda Urbana**
- **Idealista** — Portal inmobiliario
- **Fotocasa** — Portal inmobiliario

> ⚠️ Los datos mostrados son simulaciones educativas. No constituyen asesoramiento financiero.

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io)
- **Gráficos**: Plotly, PyDeck
- **Backend**: Python 3.12, SQLite, Pandas, NumPy
- **Scoring**: Modelo multifactorial con ponderación por perfil

## 📝 Licencia

MIT
