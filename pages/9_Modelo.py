import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from utils.auth import require_auth
from utils.train_model import train_and_save, load_model

st.set_page_config(page_title="Modelo ML", page_icon="🤖", layout="wide")
require_auth()

st.markdown("# 🤖 Modelo de clasificación — Random Forest")
st.caption("Predicción de decisión de inversión (COMPRAR / NEGOCIAR / DESCARTAR) basada en 9 features.")

@st.cache_resource
def _train():
    return train_and_save()

clf, metrics = _train()

if clf is None or not metrics:
    st.warning("No hay datos suficientes para entrenar el modelo.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("🎯 Accuracy", f"{metrics['accuracy']:.2%}")
col2.metric("📊 Muestras totales", f"{metrics['n_samples']:,}")
col3.metric("🧪 Test set", f"{metrics['n_test']:,}")

st.divider()

# ── Feature Importance ──
st.markdown("## Importancia de features")
fi_df = pd.DataFrame(metrics["feature_importance"])
fig_fi = px.bar(
    fi_df, x="importance", y="feature", orientation="h",
    labels={"importance": "Importancia", "feature": "Feature"},
    color="importance", color_continuous_scale="viridis",
    height=400,
)
fig_fi.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_fi, width="stretch")

st.divider()

# ── Classification Report ──
st.markdown("## Reporte de clasificación")
report = metrics["classification_report"]
report_rows = []
for cls_name, cls_data in report.items():
    if cls_name in ("accuracy", "macro avg", "weighted avg"):
        continue
    if isinstance(cls_data, dict):
        report_rows.append({
            "Clase": cls_name,
            "Precision": f"{cls_data.get('precision', 0):.2%}",
            "Recall": f"{cls_data.get('recall', 0):.2%}",
            "F1-Score": f"{cls_data.get('f1-score', 0):.2%}",
            "Soporte": int(cls_data.get('support', 0)),
        })
st.dataframe(pd.DataFrame(report_rows), width="stretch")

st.divider()

# ── Confusion Matrix ──
st.markdown("## Matriz de confusión")
cm = metrics["confusion_matrix"]
labels = ["DESCARTAR", "NEGOCIAR", "COMPRAR"]
fig_cm = ff.create_annotated_heatmap(
    cm, x=labels, y=labels,
    colorscale="Blues",
    showscale=True,
)
fig_cm.update_layout(height=400)
st.plotly_chart(fig_cm, width="stretch")

st.divider()

# ── Features usadas ──
st.markdown("### Features del modelo")
feature_cols = [
    "score_descuento", "score_precio", "score_liquidez",
    "score_tamano", "score_ruido",
    "precio_total", "metros", "precio_m2", "rentabilidad_estimada",
]
st.code("\n".join(f"  • {c}" for c in feature_cols))

st.caption("Entrenado con RandomForestClassifier (100 árboles, max_depth=12). Datos históricos Idealista18 (2018).")
