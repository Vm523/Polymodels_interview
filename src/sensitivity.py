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
    plt.rcParams.update({'font.size': 10})
    n = len(sensitivity_data)
    fig, axes = plt.subplots(n, 3, figsize=(15, 3.8 * n))
    fig.suptitle('One-at-a-Time Sensitivity Analysis — Key Process Parameters', fontsize=14, fontweight='bold')

    risk_map = {'Low': 1, 'Medium': 2, 'High': 3}
    metric_cols = ['conversion', 'impurity_fraction', 'time_h2_limited_fraction']
    metric_labels = ['Conversion', 'Impurity fraction', 'H2 limited fraction']
    ref_lines = [p.CONVERSION_TARGET, p.IMPURITY_THRESHOLD, None]

    for row, (param_name, records) in enumerate(sensitivity_data.items()):
        df = pd.DataFrame(records)
        x = df['param_value'].values
        for col_idx, (metric, label, ref) in enumerate(zip(metric_cols, metric_labels, ref_lines)):
            ax = axes[row, col_idx]
            ax.plot(x, df[metric].values, marker='o', color='steelblue', linewidth=2, markersize=5)
            if ref is not None:
                ax.axhline(ref, linestyle='--', color='red', alpha=0.6)
            ax.set_xlabel(param_name.replace('_', ' '))
            ax.set_ylabel(label)
            ax.set_title(f'{label} vs {param_name.replace("_", " ").title()}', fontsize=10)
            ax.grid(True, alpha=0.3)

    plt.subplots_adjust(hspace=0.45, wspace=0.35)
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


def plot_design_space(n_points=8):
    """Plot 2D operating window: kLa vs feed rate, coloured by risk rating.

    This shows which combinations of kLa and feed rate give acceptable
    process performance — directly analogous to ICH Q8 design space concept.
    """
    from src.model import h2_saturation as h2sat
    kla_values = np.linspace(0.1, 1.5, n_points)
    feed_values = np.linspace(0.01, 0.18, n_points)

    risk_map = {'Low': 0, 'Medium': 1, 'High': 2}
    conv_grid = np.zeros((n_points, n_points))
    imp_grid = np.zeros((n_points, n_points))
    risk_grid = np.zeros((n_points, n_points))

    for i, kla in enumerate(kla_values):
        for j, feed in enumerate(feed_values):
            params = build_params({'kla': kla, 'feed_rate': feed})
            sol = run_simulation(params)
            metrics = compute_metrics(sol, params)
            risk = risk_score(metrics, params)
            conv_grid[i, j] = metrics['conversion']
            imp_grid[i, j] = metrics['impurity_fraction']
            risk_grid[i, j] = risk_map[risk]

    plt.rcParams.update({'font.size': 11})
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    fig.suptitle('Operating Window — kLa vs Feed Rate (Design Space Analysis)',
                 fontsize=13, fontweight='bold')

    KK, FF = np.meshgrid(feed_values, kla_values)

    im0 = axes[0].contourf(FF, KK, conv_grid, levels=10, cmap='RdYlGn', vmin=0.8, vmax=1.0)
    axes[0].contour(FF, KK, conv_grid, levels=[0.95], colors='black', linewidths=1.5, linestyles='--')
    plt.colorbar(im0, ax=axes[0], label='Conversion (–)')
    axes[0].set_xlabel('Feed Rate (L/min)')
    axes[0].set_ylabel('kLa (1/min)')
    axes[0].set_title('Substrate Conversion')
    axes[0].text(0.10, 1.38, '– – 95% target', fontsize=8, color='black')

    im1 = axes[1].contourf(FF, KK, imp_grid, levels=10, cmap='RdYlGn_r', vmin=0.0, vmax=0.3)
    axes[1].contour(FF, KK, imp_grid, levels=[0.05], colors='black', linewidths=1.5, linestyles='--')
    plt.colorbar(im1, ax=axes[1], label='Impurity C/(B+C) (–)')
    axes[1].set_xlabel('Feed Rate (L/min)')
    axes[1].set_ylabel('kLa (1/min)')
    axes[1].set_title('Impurity Formation')

    colours = ['#2ecc71', '#f39c12', '#e74c3c']
    cmap_risk = __import__('matplotlib.colors', fromlist=['ListedColormap']).ListedColormap(colours)
    im2 = axes[2].contourf(FF, KK, risk_grid, levels=[-0.5, 0.5, 1.5, 2.5], cmap=cmap_risk)
    cbar = plt.colorbar(im2, ax=axes[2], ticks=[0, 1, 2])
    cbar.set_ticklabels(['Low', 'Medium', 'High'])
    axes[2].set_xlabel('Feed Rate (L/min)')
    axes[2].set_ylabel('kLa (1/min)')
    axes[2].set_title('Overall Risk Rating')

    plt.subplots_adjust(left=0.06, right=0.97, bottom=0.13, top=0.88, wspace=0.45)
    path = os.path.join(FIGURES_DIR, 'design_space.png')
    plt.savefig(path, dpi=150)
    print(f'Saved: {path}')
    plt.close()


if __name__ == '__main__':
    ensure_dirs()
    print('Running sensitivity analysis...')
    sensitivity_data = {}
    for param_name, values in SENSITIVITY_PARAMS.items():
        print(f'  Varying {param_name}...')
        sensitivity_data[param_name] = run_sensitivity(param_name, values)
    plot_sensitivity(sensitivity_data)
    save_sensitivity_summary(sensitivity_data)
    print('Running design space analysis (this takes ~30 seconds)...')
    plot_design_space(n_points=8)
    print('Done.')
