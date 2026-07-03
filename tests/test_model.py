import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np


class TestModelPipeline:
    def test_load_data_returns_nonempty(self):
        from utils.train_model import load_data
        df = load_data()
        assert not df.empty, "load_data() returned empty DataFrame"
        assert "decision" in df.columns
        assert df["decision"].notna().all()
        assert set(df["decision"].unique()).issubset({"COMPRAR", "NEGOCIAR", "DESCARTAR"})

    def test_train_runs_and_returns_model(self):
        from utils.train_model import load_data, train
        df = load_data()
        if df.empty:
            return
        clf, metrics = train(df)
        assert clf is not None
        assert metrics["accuracy"] > 0
        assert "feature_importance" in metrics
        assert "confusion_matrix" in metrics
        assert len(metrics["feature_importance"]) == 8

    def test_decision_distribution_reasonable(self):
        from utils.train_model import load_data
        df = load_data()
        if df.empty:
            return
        vc = df["decision"].value_counts()
        total = len(df)
        for decision in ("COMPRAR", "NEGOCIAR", "DESCARTAR"):
            pct = vc.get(decision, 0) / total
            assert 0.05 <= pct <= 0.90, f"{decision}: {pct:.1%} fuera de rango esperado"

    def test_predict_returns_valid_labels(self):
        from utils.train_model import train, load_data
        from utils.explorer_service import get_page, predict_page

        df = load_data()
        if df.empty:
            return
        clf, _ = train(df)

        sample = get_page({}, 0, 10)
        if sample.empty:
            return
        preds = predict_page(sample)
        assert len(preds) == len(sample)
        for p in preds:
            assert p in ("COMPRAR", "NEGOCIAR", "DESCARTAR")
