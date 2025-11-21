import numpy as np
from scipy import stats
from .constants import N_CHI_BINS


def compute_tests_region(values_A, values_B):
    """
    Compute set of statistical test responses between two 1D arrays.
    Returns dict with keys: DoB, T, F, L, U, KS, v2
    """
    # guard against empty
    if values_A.size == 0 or values_B.size == 0:
        return {
            "DoB": 0.0, "T": 0.0, "F": 1.0, "L": 0.0,
            "U": 0.0, "KS": 0.0, "v2": 0.0
        }

    a = values_A.astype(float)
    b = values_B.astype(float)

    # DoB
    dob = abs(a.mean() - b.mean())

    # student t stat (Welch's t-statistic magnitude)
    sa = a.var(ddof=1) if a.size > 1 else 0.0
    sb = b.var(ddof=1) if b.size > 1 else 0.0
    na = a.size
    nb = b.size
    denom = np.sqrt((sa / na if na>0 else 0) + (sb / nb if nb>0 else 0))
    t_stat = abs(a.mean() - b.mean()) / (denom + 1e-12)

    # Fisher F
    if sa <= 0 and sb <= 0:
        f_stat = 1.0
    elif sb == 0:
        f_stat = np.inf
    else:
        f_stat = max(sa / (sb + 1e-12), sb / (sa + 1e-12))

    # Likelihood-like (approx): -N * log( var_ratio )
    var_ratio = (sa + 1e-12) / (sb + 1e-12)
    L = - (na + nb) * np.log(4.0 * var_ratio + 1e-12)

    # Mann-Whitney U
    try:
        u_res = stats.mannwhitneyu(a, b, alternative='two-sided')
        Ustat = u_res.statistic
    except Exception:
        Ustat = 0.0

    # KS D statistic
    try:
        ks_res = stats.ks_2samp(a, b)
        KSD = ks_res.statistic
    except Exception:
        KSD = 0.0

    # Chi-square style v2
    R, _ = np.histogram(a, bins=N_CHI_BINS, range=(0, 255))
    S, _ = np.histogram(b, bins=N_CHI_BINS, range=(0, 255))
    denom = (R + S).astype(float)
    mask_pos = denom > 0
    v2 = np.sum(((R - S) ** 2)[mask_pos] / denom[mask_pos])

    return {
        "DoB": dob,
        "T": t_stat,
        "F": f_stat if np.isfinite(f_stat) else np.max([sa, sb]) * 1e3,
        "L": L,
        "U": Ustat,
        "KS": KSD,
        "v2": v2
    }

