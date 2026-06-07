"""Utility functions shared across simulation scripts."""

import os
import numpy as np
import pandas as pd


FIGURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'results', 'figures')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')


def ensure_dirs():
    """Create output directories if they do not exist."""
    os.makedirs(FIGURES_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)


def compute_metrics(sol, params):
    """Compute key process metrics from an ODE solution.

    Returns a dict with conversion, yield, selectivity, impurity fraction,
    min dissolved H2, and time fraction spent under H2 limitation.
    """
    A = sol.y[0]
    B = sol.y[1]
    C = sol.y[2]
    H2 = sol.y[3]
    V = sol.y[4]

    feed_rate = params['feed_rate']
    feed_conc_a = params['feed_conc_a']
    t = sol.t

    total_a_fed = feed_rate * feed_conc_a * t[-1]
    moles_a_remaining = A[-1] * V[-1]
    moles_b = B[-1] * V[-1]
    moles_c = C[-1] * V[-1]

    conversion = 1.0 - moles_a_remaining / (total_a_fed + 1e-12)
    conversion = min(max(conversion, 0.0), 1.0)

    total_product = moles_b + moles_c
    selectivity = moles_b / (total_product + 1e-12)
    impurity_fraction = moles_c / (total_product + 1e-12)

    min_h2 = float(np.min(H2))
    threshold = params.get('h2_lim_threshold', 0.01)
    dt = np.diff(t)
    time_h2_limited = float(np.sum(dt[H2[:-1] < threshold])) / t[-1]

    return {
        'conversion': conversion,
        'selectivity': selectivity,
        'impurity_fraction': impurity_fraction,
        'min_h2': min_h2,
        'time_h2_limited_fraction': time_h2_limited,
    }


def risk_score(metrics, params):
    """Return 'Low', 'Medium', or 'High' risk rating based on process metrics."""
    score = 0

    if metrics['conversion'] < params.get('conversion_target', 0.95):
        score += 2
    elif metrics['conversion'] < 0.99:
        score += 1

    if metrics['impurity_fraction'] > 0.15:
        score += 3
    elif metrics['impurity_fraction'] > params.get('impurity_threshold', 0.05):
        score += 2
    elif metrics['impurity_fraction'] > 0.02:
        score += 1

    if metrics['time_h2_limited_fraction'] > 0.3:
        score += 2
    elif metrics['time_h2_limited_fraction'] > 0.1:
        score += 1

    if score <= 1:
        return 'Low'
    elif score <= 3:
        return 'Medium'
    else:
        return 'High'


def build_params(overrides=None):
    """Build parameter dict from defaults with optional overrides."""
    import src.parameters as p
    from src.model import h2_saturation

    defaults = {
        'k1': p.K1,
        'k2': p.K2,
        'kla': p.KLA,
        'h2_pressure': p.H2_PRESSURE,
        'h2_sat': h2_saturation(p.H2_PRESSURE, p.H2_SAT_BASE),
        'feed_rate': p.FEED_RATE,
        'feed_conc_a': p.FEED_CONC_A,
        'v0': p.V0,
        'h2_lim_threshold': p.H2_LIMITATION_THRESHOLD,
        'conversion_target': p.CONVERSION_TARGET,
        'impurity_threshold': p.IMPURITY_THRESHOLD,
        't_end': p.T_END,
        'n_eval': p.N_EVAL,
    }
    if overrides:
        defaults.update(overrides)
    return defaults
