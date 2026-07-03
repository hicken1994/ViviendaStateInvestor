import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from utils.profiles import compute_score_with_profile, get_perfil


def _row(**overrides) -> pd.Series:
    data = {
        "descuento_pct": 20.0,
        "precio_m2": 3000.0,
        "precio_m2_barrio": 4000.0,
        "metros": 70.0,
        "precio_total": 210000.0,
        "noise_score": 30.0,
    }
    data.update(overrides)
    return pd.Series(data)


class TestScoring:
    def test_comprar_high_discount(self):
        perfil = get_perfil("intermedio")
        result = compute_score_with_profile(_row(descuento_pct=35), perfil)
        assert result["decision"] == "COMPRAR"
        assert result["score_total"] >= 60

    def test_descartar_low_discount(self):
        perfil = get_perfil("intermedio")
        result = compute_score_with_profile(
            _row(descuento_pct=5, precio_m2=4000, precio_m2_barrio=4000,
                 metros=45, noise_score=80),
            perfil,
        )
        assert result["decision"] == "DESCARTAR"

    def test_negociar_mid_discount(self):
        perfil = get_perfil("intermedio")
        result = compute_score_with_profile(_row(descuento_pct=15, precio_m2=3800, precio_m2_barrio=4000), perfil)
        assert result["decision"] in ("COMPRAR", "NEGOCIAR")

    def test_profile_basico_requires_higher_score(self):
        basico = get_perfil("basico")
        intermedio = get_perfil("intermedio")
        row = _row(descuento_pct=25)
        r_basico = compute_score_with_profile(row, basico)
        r_inter = compute_score_with_profile(row, intermedio)
        assert r_basico["score_total"] <= r_inter["score_total"]

    def test_avanzado_tolerates_lower_score(self):
        avanzado = get_perfil("avanzado")
        result = compute_score_with_profile(
            _row(descuento_pct=10, precio_m2=4000, precio_m2_barrio=4000,
                 metros=45, noise_score=80),
            avanzado,
        )
        assert result["decision"] in ("NEGOCIAR", "DESCARTAR")

    def test_score_descuento_capped_at_40(self):
        perfil = get_perfil("intermedio")
        result = compute_score_with_profile(_row(descuento_pct=50), perfil)
        assert result["score_descuento"] <= 40

    def test_rentabilidad_positive(self):
        perfil = get_perfil("intermedio")
        result = compute_score_with_profile(_row(precio_m2_barrio=5000, precio_total=200000, metros=80), perfil)
        assert result["rentabilidad_estimada"] > 0

    def test_all_profiles_return_same_structure(self):
        row = _row()
        for name in ("basico", "intermedio", "avanzado"):
            perfil = get_perfil(name)
            result = compute_score_with_profile(row, perfil)
            for key in ("score_total", "score_descuento", "score_precio",
                        "score_liquidez", "score_tamano", "score_ruido",
                        "rentabilidad_estimada", "decision"):
                assert key in result, f"{key} missing in {name}"
