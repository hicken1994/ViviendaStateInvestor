from utils.profiles import compute_score_with_profile, PERFILES


def compute_investment_metrics(row, perfil=None):
    if perfil is None:
        perfil = PERFILES["intermedio"]
    return compute_score_with_profile(row, perfil)