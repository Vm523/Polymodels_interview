"""Compare multiple fed-batch hydrogenation scenarios and save outputs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from src.model import h2_saturation
from src.simulate import run_simulation
from src.utils import ensure_dirs, compute_metrics, risk_score, build_params, FIGURES_DIR, RESULTS_DIR
import src.parameters as p


SCENARIOS = {
    'base_case': {},
    'high_feed_rate': {'feed_rate': 0.15},
    'low_h2_transfer': {'kla': 0.2},
    'high_catalyst': {'k1': 3.0, 'k2': 0.05},
    'high_h2_pressure': {
        'h2_pressure': 6.0,
        'h2_sat': h2_saturation(6.0, p.H2_SAT_BASE),
    },
}


def run_all_scenarios():
    """Run all scenarios and return dict of {name: (sol, metrics, risk)}."""
    results = {}
    for name, overrides in SCENARIOS.items():
        params = build_params(overrides)
        sol = run_simulation(params)
        metrics = compute_metrics(sol, params)
        risk = risk_score(metrics, params)
        results[name] = (sol, metrics, risk)
        print(f'{name}: conversion={metrics["conversion"]:.3f}, impurity={metrics["impurity_fraction"]:.3f}, risk={risk}')
    return results


def plot_scenario_comparison(results):
    """Bar chart comparing key metrics across scenarios."""
    names = list(results.keys())
    conversions = [results[n][1]['conversion'] for n in names]
    impurities = [results[n][1]['impurity_fraction'] for n in names]
    h2_lim = [results[n][1]['time_h2_limited_fraction'] for n in names]
    risk_map = {'Low': 1, 'Medium': 2, 'High': 3}
    risks = [risk_map[results[n][2]] for n in names]

    x = np.arange(len(names))
    width = 0.2
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - 1.5 * width, conversions, width, label='Conversion', color='steelblue')
    ax.bar(x - 0.5 * width, impurities, width, label='Impurity fraction', color='tomato')
    ax.bar(x + 0.5 * width, h2_lim, width, label='H2 limited fraction', color='darkorange')
    ax.bar(x + 1.5 * width, [r / 3.0 for r in risks], width, label='Risk (norm)', color='purple', alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels([n.replace('_', ' ') for n in names], rotation=15, ha='right')
    ax.set_ylabel('Value')
    ax.set_title('Scenario Comparison — Key Process Metrics')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(p.CONVERSION_TARGET, linestyle='--', color='green', alpha=0.5, label='Conv. target')
    ax.axhline(p.IMPURITY_THRESHOLD, linestyle='--', color='red', alpha=0.5, label='Imp. threshold')

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, 'scenario_comparison.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f'Saved: {path}')
    plt.close()


def plot_concentration_overlay(results):
    """Overlay product B profiles for all scenarios."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    colours = ['steelblue', 'tomato', 'seagreen', 'darkorange', 'purple']
    for i, (name, (sol, _, _)) in enumerate(results.items()):
        c = colours[i % len(colours)]
        label = name.replace('_', ' ')
        axes[0].plot(sol.t, sol.y[1], label=label, color=c)
        axes[1].plot(sol.t, sol.y[3], label=label, color=c)

    axes[0].set_xlabel('Time (min)')
    axes[0].set_ylabel('B concentration (mol/L)')
    axes[0].set_title('Product B — Scenario Overlay')
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    axes[1].set_xlabel('Time (min)')
    axes[1].set_ylabel('Dissolved H2 (mol/L)')
    axes[1].set_title('Dissolved H2 — Scenario Overlay')
    axes[1].axhline(p.H2_LIMITATION_THRESHOLD, linestyle='--', color='red', alpha=0.6)
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, 'scenario_overlay.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f'Saved: {path}')
    plt.close()


def save_scenario_summary(results):
    """Save scenario metrics to CSV."""
    rows = []
    for name, (_, metrics, risk) in results.items():
        row = {'scenario': name, 'risk': risk}
        row.update(metrics)
        rows.append(row)
    df = pd.DataFrame(rows)
    path = os.path.join(RESULTS_DIR, 'scenario_summary.csv')
    df.to_csv(path, index=False)
    print(f'Saved: {path}')


if __name__ == '__main__':
    ensure_dirs()
    print('Running scenario comparison...')
    results = run_all_scenarios()
    plot_scenario_comparison(results)
    plot_concentration_overlay(results)
    save_scenario_summary(results)
    print('Done.')
