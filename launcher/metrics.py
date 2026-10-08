"""Climatological and Statistical Validation Metrics for CDT Outputs.

Computes continuous metrics (KGE, RMSE, MAE, R², PBIAS) and
categorical contingency metrics (POD, FAR, FBI, ETS, HSS) for research publications.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple, Union

import numpy as np


def compute_continuous_metrics(
    obs: np.ndarray, sim: np.ndarray
) -> Dict[str, float]:
    """Calculate continuous performance metrics between observations and merged grids.

    Args:
        obs: 1D array of observed station values.
        sim: 1D array of simulated/merged grid values at station coordinates.

    Returns:
        Dictionary with RMSE, MAE, R2, PBIAS, and KGE.
    """
    mask = ~np.isnan(obs) & ~np.isnan(sim)
    o = obs[mask]
    s = sim[mask]

    if len(o) < 2:
        return {"n": len(o), "rmse": np.nan, "mae": np.nan, "r2": np.nan, "pbias": np.nan, "kge": np.nan}

    # Mean and standard deviation
    mean_o = np.mean(o)
    mean_s = np.mean(s)
    std_o = np.std(o, ddof=1)
    std_s = np.std(s, ddof=1)

    # Correlation coefficient (r)
    if std_o > 1e-12 and std_s > 1e-12:
        r = np.corrcoef(o, s)[0, 1]
    else:
        r = 0.0

    r2 = r ** 2

    # MAE and RMSE
    mae = np.mean(np.abs(s - o))
    rmse = np.sqrt(np.mean((s - o) ** 2))

    # Percent Bias (PBIAS)
    sum_o = np.sum(o)
    if abs(sum_o) > 1e-12:
        pbias = 100.0 * np.sum(s - o) / sum_o
    else:
        pbias = 0.0

    # Kling-Gupta Efficiency (KGE, 2012 revised: beta=bias ratio, gamma=variability ratio)
    if std_o > 1e-12 and mean_o > 1e-12 and std_s > 1e-12 and mean_s > 1e-12:
        beta = mean_s / mean_o
        gamma = (std_s / mean_s) / (std_o / mean_o)
        kge = 1.0 - np.sqrt((r - 1.0) ** 2 + (beta - 1.0) ** 2 + (gamma - 1.0) ** 2)
    else:
        kge = np.nan

    return {
        "n_samples": int(len(o)),
        "r": float(r),
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
        "pbias": float(pbias),
        "kge": float(kge),
    }


def compute_categorical_metrics(
    obs: np.ndarray, sim: np.ndarray, threshold: float = 1.0
) -> Dict[str, float]:
    """Calculate contingency table and categorical skill scores for precipitation.

    Args:
        obs: Observed rainfall values (mm).
        sim: Estimated/merged rainfall values (mm).
        threshold: Rainfall event threshold (default: 1.0 mm).

    Returns:
        Dictionary with POD, FAR, FBI, ETS, and HSS.
    """
    mask = ~np.isnan(obs) & ~np.isnan(sim)
    o = obs[mask] >= threshold
    s = sim[mask] >= threshold

    hits = int(np.sum(o & s))            # Hits (a)
    false_alarms = int(np.sum(~o & s))   # False Alarms (b)
    misses = int(np.sum(o & ~s))         # Misses (c)
    correct_neg = int(np.sum(~o & ~s))   # Correct Negatives (d)
    total = len(o)

    if total == 0:
        return {"hits": 0, "false_alarms": 0, "misses": 0, "correct_negatives": 0,
                "pod": np.nan, "far": np.nan, "fbi": np.nan, "ets": np.nan, "hss": np.nan}

    # Probability of Detection (POD) = Hits / (Hits + Misses)
    pod = hits / (hits + misses) if (hits + misses) > 0 else np.nan

    # False Alarm Ratio (FAR) = False Alarms / (Hits + False Alarms)
    far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else np.nan

    # Frequency Bias Index (FBI) = (Hits + False Alarms) / (Hits + Misses)
    fbi = (hits + false_alarms) / (hits + misses) if (hits + misses) > 0 else np.nan

    # Equitable Threat Score (ETS)
    hits_random = ((hits + misses) * (hits + false_alarms)) / total
    denom_ets = hits + misses + false_alarms - hits_random
    ets = (hits - hits_random) / denom_ets if denom_ets > 0 else np.nan

    # Heidke Skill Score (HSS)
    expected_correct = ((hits + misses) * (hits + false_alarms) + (correct_neg + misses) * (correct_neg + false_alarms)) / total
    denom_hss = total - expected_correct
    hss = ((hits + correct_neg) - expected_correct) / denom_hss if denom_hss > 0 else np.nan

    return {
        "total_events": total,
        "hits": hits,
        "false_alarms": false_alarms,
        "misses": misses,
        "correct_negatives": correct_neg,
        "pod": float(pod),
        "far": float(far),
        "fbi": float(fbi),
        "ets": float(ets),
        "hss": float(hss),
    }
