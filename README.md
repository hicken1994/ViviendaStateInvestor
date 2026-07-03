# Vivienda AI — End-to-end Data Pipeline with ML Classification

**86,183 real properties · Multi-factor scoring · Random Forest classifier · Streamlit + Supabase**

A production-grade data engineering and machine learning portfolio project. Ingests raw open data from multiple sources, transforms it through an ETL pipeline, persists it in Supabase (PostgreSQL), caches locally in SQLite, and serves interactive ML-powered predictions via a Streamlit app.

---

## Architecture

```
Idealista18 (RDA) ─┐
                   ├──► ETL (utils/etl.py) ──► Supabase ──► Sync ──► SQLite ──► Streamlit
Kaggle (CSV) ─────┘                        PostgreSQL       cache          UI
                                                              │
                                                         RandomForest
                                                         Classifier
                                                         (scikit-learn)
```

- **Ingestion**: `utils/etl.py` reads Idealista18 (94K rows in RDA format) and Kaggle Madrid dataset (CSV), transforms to unified schema, uploads to Supabase via batch REST upsert
- **Storage**: Supabase (PostgreSQL) as persistent source of truth, SQLite as local cache with WAL mode
- **Sync**: `utils/supabase_sync.py` pulls all 6 tables from Supabase → local SQLite with pagination (1000 rows/request)
- **Scoring**: Rule-based multi-factor system (utils/profiles.py) — 5 dimensions weighted by investor profile
- **ML**: RandomForestClassifier (100 trees, 9 features) trained on all 86K properties — predicts COMPRAR/NEGOCIAR/DESCARTAR with metrics displayed in the app

---

## ML Model

| Metric | Value |
|---|---|
| Algorithm | RandomForestClassifier |
| Features | 9 (score_descuento, score_precio, score_liquidez, score_tamano, score_ruido, precio_total, metros, precio_m2, rentabilidad_estimada) |
| Target | decision (COMPRAR / NEGOCIAR / DESCARTAR) |
| Train/Test split | 80/20 stratified |
| Hyperparameters | n_estimators=100, max_depth=12 |

View live metrics, feature importance, classification report, and confusion matrix at `pages/9_Modelo.py` in the app.

---

## Dataset

- **86,183 properties** across Madrid
- **21 districts** with rental prices per m²
- Sources: Idealista18 open dataset (2018) + Kaggle Madrid real estate
- Rental prices: `barrio_rent` table with 21 barrios
- All data persisted in Supabase, synced to local SQLite on app boot

---

## Scoring system

5 dimensions, weighted by investor profile (Básico / Intermedio / Avanzado):

| Dimension | Max | Description |
|---|---|---|
| Descuento | 40 pts | Price vs market value in barrio |
| Precio vs Barrio | 25 pts | Price per m² vs barrio average |
| Liquidez | 15 pts | Rental liquidity (50-90 m² optimal) |
| Tamaño | 10 pts | Surface area (>60 m² scores higher) |
| Ruido | 10 pts | Estimated noise level of zone |

---

## Tech stack

- **Frontend**: Streamlit 1.55
- **Visualization**: Plotly, PyDeck
- **Backend**: Python 3.14, SQLite (WAL mode, connection pooling)
- **Database**: Supabase (PostgreSQL with RLS) + SQLite local cache
- **Auth**: Supabase Auth (email/password, magic link, Google OAuth)
- **ML**: scikit-learn (RandomForestClassifier)
- **Infrastructure**: Streamlit Cloud deployment

---

## Run locally

```bash
git clone https://github.com/julianrincon/viviendastateinvestor.git
cd viviendastateinvestor
pip install -r requirements.txt
streamlit run app.py
```

Requires a `.streamlit/secrets.toml` with Supabase credentials. See `supabase_schema.sql` for the database schema.

---

## Project structure

```
├── app.py                    # Auth + DB init + redirect
├── pages/
│   ├── 0_Bienvenida.py       # Onboarding tour
│   ├── 1_Radar.py            # Radar with semáforo cards
│   ├── 2_Mapa.py             # Heatmap (PyDeck)
│   ├── 3_propiedad.py        # Property analysis + PDF export
│   ├── 4_Analisis_Detallado.py  # AI Copilot
│   ├── 5_Comparador.py       # Side-by-side comparison
│   ├── 6_Alertas.py          # Notifications + watchlist
│   ├── 7_Mi_Cuenta.py        # User profile
│   ├── 8_Admin.py            # Admin panel
│   └── 9_Modelo.py           # ML model metrics
├── utils/
│   ├── auth.py               # Supabase Auth (email, magic link, Google)
│   ├── connection.py         # SQLite connection manager
│   ├── db.py                 # DB operations, market simulation
│   ├── services.py           # Query layer (typed SQL)
│   ├── profiles.py           # Investment profiles + scoring
│   ├── train_model.py        # RandomForest training + save/load
│   ├── etl.py                # ETL pipeline (Idealista18 + Kaggle → Supabase)
│   ├── supabase_sync.py      # Supabase → SQLite sync with pagination
│   ├── migrations.py         # Schema migrations (v1-v7)
│   ├── pdf_report.py         # FPDF2 report generation
│   ├── notifications.py      # Real opportunity detection
│   ├── email_notifier.py     # SendGrid email alerts
│   └── user_store.py         # Supabase preferences + watchlist CRUD
├── components/
│   ├── sidebar.py            # Shared sidebar with nav + notifications
│   ├── footer.py             # Data source footer
│   └── score_help.py         # Score breakdown UI
├── supabase_schema.sql       # PostgreSQL DDL
├── requirements.txt          # Dependencies
└── model/                    # Trained model artifacts (generated)
```

---

## Key architectural decisions

- **Hybrid storage**: Supabase as persistent truth, SQLite as read cache — avoids rewriting the data access layer while keeping data alive across Streamlit Cloud deploys
- **Batch upsert**: 300 rows/batch for 86K properties via REST API (~60s total)
- **Paginated sync**: Supabase free tier caps at 1000 rows/response — `range()` in loop fetches all rows
- **Rule-based scoring + ML**: Rule system is transparent and explainable; ML adds predictive power. Both coexist in the app
- **Same-page PDF generation**: FPDF2 (pure Python, no system deps) works on Streamlit Cloud without wkhtmltopdf

---

## What I learned

- Streamlit's single-threaded model shapes the entire architecture — caching, session state placement, and rerun management matter
- Supabase REST API is strict about type casting (INTEGER columns reject float JSON) — ETL must cast before upload
- FPDF2's built-in fonts are Latin-1 only — Unicode text needs explicit TTF font registration
- Magic link auth requires zero config with Supabase; Google OAuth needs client ID/secret setup
- 86K properties + 9 features fit in <10MB — RandomForest trains in seconds, model file is ~2MB
- The product didn't sell, but the architecture is a stronger career signal than any "SaaS that made €0"
