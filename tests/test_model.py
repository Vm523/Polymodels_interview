"""Basic tests for the fed-batch hydrogenation model."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np

from src.model import odes, reaction_rates, h2_saturation
from src.utils import compute_metrics, risk_score, build_params
from src.simulate import run_simulation


def test_h2_saturation_scales_with_pressure():
    assert h2_saturation(2.0, 0.05) == pytest.approx(0.10)
    assert h2_saturation(4.0, 0.05) == pytest.approx(0.20)


def test_reaction_rates_zero_when_no_h2():
    r1, r2 = reaction_rates(A=1.0, B=1.0, H2=0.0, k1=0.1, k2=0.01)
    assert r1 == 0.0
    assert r2 == 0.0


def test_reaction_rates_positive():
    r1, r2 = reaction_rates(A=1.0, B=0.5, H2=0.05, k1=0.08, k2=0.004)
    assert r1 > 0
    assert r2 > 0


def test_odes_volume_increases():
    params = build_params()
    y0 = [0.0, 0.0, 0.0, 0.0, 1.0]
    dy = odes(0.0, y0, params)
    assert dy[4] == pytest.approx(params['feed_rate'])


def test_simulation_runs_without_error():
    params = build_params()
    sol = run_simulation(params)
    assert sol.success, f'Solver failed: {sol.message}'


def test_simulation_volume_increases():
    params = build_params()
    sol = run_simulation(params)
    V = sol.y[4]
    assert V[-1] > V[0]


def test_metrics_conversion_in_range():
    params = build_params()
    sol = run_simulation(params)
    metrics = compute_metrics(sol, params)
    assert 0.0 <= metrics['conversion'] <= 1.0


def test_metrics_impurity_in_range():
    params = build_params()
    sol = run_simulation(params)
    metrics = compute_metrics(sol, params)
    assert 0.0 <= metrics['impurity_fraction'] <= 1.0


def test_risk_score_low_for_base_case():
    params = build_params()
    sol = run_simulation(params)
    metrics = compute_metrics(sol, params)
    rating = risk_score(metrics, params)
    assert rating in ('Low', 'Medium', 'High')


def test_high_feed_rate_raises_h2_limitation():
    base_params = build_params()
    high_feed_params = build_params({'feed_rate': 0.18})
    base_sol = run_simulation(base_params)
    high_sol = run_simulation(high_feed_params)
    base_metrics = compute_metrics(base_sol, base_params)
    high_metrics = compute_metrics(high_sol, high_feed_params)
    assert high_metrics['time_h2_limited_fraction'] >= base_metrics['time_h2_limited_fraction']


def test_higher_pressure_increases_h2_sat():
    import src.parameters as p
    from src.model import h2_saturation
    low_p_params = build_params({'h2_pressure': 1.0, 'h2_sat': h2_saturation(1.0, p.H2_SAT_BASE)})
    high_p_params = build_params({'h2_pressure': 6.0, 'h2_sat': h2_saturation(6.0, p.H2_SAT_BASE)})
    assert high_p_params['h2_sat'] > low_p_params['h2_sat']
