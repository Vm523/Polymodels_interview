"""One-at-a-time sensitivity analysis for fed-batch hydrogenation model."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.model import h2_saturation
from src.simulate import run_simulation
from src.utils import ensure_dirs, compute_metrics, risk_score, build_params, FIGURES_DIR, RESULTS_DIR
import src.parameters as p


SENSITIVITY_PARAMS = {
    'feed_rate': np.linspace(0.01, 0.2, 10),
    'h2_pressure': np.linspace(1.0, 8.0, 10),
    'kla': np.linspace(0.1, 2.0, 10),
    'k1': np.linspace(0.3, 3.0, 10),
}


def run_sensitivity(param_name, values):
    """Vary one parameter across given values, return list of metric dicts."""
    results = []
    for v in values:
        if param_name == 'h2_pressure':
            overrides = {'h2_pressure': v, 'h2_sat': h2_saturation(v, p.H2_SAT_BASE)}
        else:
            overrides = {param_name: v}
        params = build_params(overrides)
        sol = run_simulation(params)
        metrics = compute_metrics(sol, params)
        risk = risk_score(metrics, params)
        results.append({'param_value': v, 'risk': risk, **metrics})
    return results


def plot_sensitivity(sensitivity_data):
    """Plot sensitivity of conversion, impurity and H2 limitation for each parameter."""
    n = len(sensitivity_data)
    fig, axes = plt.subplots(n, 3, figsize=(14, 3.5 * n))
    fig.suptitle('One-at-a-Time Sensitivity Analysis', fontsize=13)

    risk_map = {'Low': 1, 'Medium': 2, 'High': 3}
    metric_cols = ['conversion', 'impurity_fraction', 'time_h2_limited_fraction']
    metric_labels = ['Conversion', 'Impurity fraction', 'H2 limited fraction']
    ref_lines = [p.CONVERSION_TARGET, p.IMPURITY_THRESHOLD, None]

    for row, (param_name, records) in enumerate(sensitivity_data.items()):
        df = pd.DataFrame(records)
        x = df['param_value'].values
        for col_idx, (metric, label, ref) in enumerate(zip(metric_cols, metric_labels, ref_lines)):
            ax = axes[row, col_idx]
            ax.plot(x, df[metric].values, marker='o', color='steelblue', markersize=4)
            if ref is not None:
                ax.axhline(ref, linestyle='--', color='red', alpha=0.6)
            ax.set_xlabel(param_name.replace('_', ' '))
            ax.set_ylabel(label)
            ax.set_title(f'{label} vs {param_name.replace("_", " ")}')
            ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, 'sensitivity_analysis.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f'Saved: {path}')
    plt.close()


def save_sensitivity_summary(sensitivity_data):
    """Save all sensitivity results to CSV."""
    rows = []
    for param_name, records in sensitivity_data.items():
        for rec in records:
            rows.append({'parameter': param_name, **rec})
    df = pd.DataFrame(rows)
    path = os.path.join(RESULTS_DIR, 'sensitivity_summary.csv')
    df.to_csv(path, index=False)
    print(f'Saved: {path}')


if __name__ == '__main__':
    ensure_dirs()
    print('Running sensitivity analysis...')
    sensitivity_data = {}
    for param_name, values in SENSITIVITY_PARAMS.items():
        print(f'  Varying {param_name}...')
        sensitivity_data[param_name] = run_sensitivity(param_name, values)
    plot_sensitivity(sensitivity_data)
    save_sensitivity_summary(sensitivity_data)
    print('Done.')
