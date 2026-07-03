import json
import os
import pickle
import logging

import numpy as np
import pandas as pd

from utils.connection import get_conn_ro

logger = logging.getLogger(__name__)

MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "classifier.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")


def _ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    with get_conn_ro() as conn:
        df = pd.read_sql("""
            SELECT
                score_descuento, score_precio, score_liquidez,
                score_tamano,
                precio_total, metros, precio_m2, rentabilidad_estimada,
                opportunity_score
            FROM oportunidades
            WHERE opportunity_score IS NOT NULL
        """, conn)
    if df.empty:
        return df
    df["decision"] = df["opportunity_score"].apply(
        lambda s: "COMPRAR" if s >= 70 else ("NEGOCIAR" if s >= 50 else "DESCARTAR")
    )
    return df


def train(df: pd.DataFrame) -> dict:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.model_selection import train_test_split

    feature_cols = [
        "score_descuento", "score_precio", "score_liquidez",
        "score_tamano",
        "precio_total", "metros", "precio_m2", "rentabilidad_estimada",
    ]

    X = df[feature_cols].copy()
    y = df["decision"].copy()

    for col in X.select_dtypes(include="object").columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    X = X.fillna(0)

    label_map = {"COMPRAR": 2, "NEGOCIAR": 1, "DESCARTAR": 0}
    y_num = y.map(label_map)
    valid = y_num.notna()
    X = X[valid]
    y_num = y_num[valid].astype(int)

    present_labels = sorted(y_num.unique())
    if len(present_labels) < 2:
        return None, {"accuracy": 0, "error": "Solo una clase presente en los datos"}

    stratify_param = y_num if y_num.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_num, test_size=0.2, random_state=42, stratify=stratify_param
    )

    clf = RandomForestClassifier(
        n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
    report = classification_report(y_test, y_pred, output_dict=True, labels=[0, 1, 2], target_names=["DESCARTAR", "NEGOCIAR", "COMPRAR"], zero_division=0)

    feature_importance = [
        {"feature": col, "importance": round(float(v), 4)}
        for col, v in sorted(zip(feature_cols, clf.feature_importances_), key=lambda x: -x[1])
    ]

    metrics = {
        "accuracy": round(float(acc), 4),
        "n_samples": int(len(df)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "feature_importance": feature_importance,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
    }

    return clf, metrics


def save_model(clf, metrics: dict):
    _ensure_model_dir()
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Modelo guardado en %s", MODEL_PATH)


def load_model():
    if not os.path.exists(MODEL_PATH):
        return None, None
    with open(MODEL_PATH, "rb") as f:
        clf = pickle.load(f)
    metrics = {}
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH) as f:
            metrics = json.load(f)
    return clf, metrics


def train_and_save():
    df = load_data()
    if df.empty:
        logger.warning("No hay datos para entrenar")
        return None, None
    clf, metrics = train(df)
    if clf is None:
        logger.warning("Entrenamiento fallo: %s", metrics.get("error", "error desconocido"))
        return None, metrics
    save_model(clf, metrics)
    return clf, metrics
