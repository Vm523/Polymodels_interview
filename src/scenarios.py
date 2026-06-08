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
    labels = [n.replace('_', ' ').replace('case','\ncase').title() for n in names]
    conversions = [results[n][1]['conversion'] for n in names]
    impurities = [results[n][1]['impurity_fraction'] for n in names]
    h2_lim = [results[n][1]['time_h2_limited_fraction'] * 100 for n in names]
    risks = [results[n][2] for n in names]
    risk_colours = {'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'}

    plt.rcParams.update({'font.size': 11})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Scenario Comparison — Fed-Batch Hydrogenation', fontsize=14, fontweight='bold')

    x = np.arange(len(names))
    width = 0.35
    bars1 = ax1.bar(x - width/2, conversions, width, label='Conversion (–)', color='#3498db', alpha=0.85)
    bars2 = ax1.bar(x + width/2, impurities, width, label='Impurity C/(B+C) (–)', color='#e74c3c', alpha=0.85)
    ax1.axhline(p.CONVERSION_TARGET, linestyle='--', color='#3498db', alpha=0.7, linewidth=1.5, label=f'Conv. target ({p.CONVERSION_TARGET*100:.0f}%)')
    ax1.axhline(p.IMPURITY_THRESHOLD, linestyle='--', color='#e74c3c', alpha=0.7, linewidth=1.5, label=f'Impurity limit ({p.IMPURITY_THRESHOLD*100:.0f}%)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel('Fraction (–)')
    ax1.set_title('Conversion and Impurity by Scenario')
    ax1.legend(fontsize=9)
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(0, 1.1)

    bar_colours = [risk_colours[r] for r in risks]
    ax2.bar(x, h2_lim, color=bar_colours, alpha=0.85, edgecolor='white')
    ax2.axhline(10, linestyle='--', color='grey', alpha=0.7, linewidth=1.5, label='10% threshold')
    for i, (val, risk) in enumerate(zip(h2_lim, risks)):
        ax2.text(i, val + 1, risk, ha='center', va='bottom', fontsize=9, fontweight='bold', color=risk_colours[risk])
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel('Time H2-limited (% of batch)')
    ax2.set_title('H2 Mass Transfer Limitation by Scenario')
    ax2.legend(fontsize=9)
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, 'scenario_comparison.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f'Saved: {path}')
    plt.close()


def plot_concentration_overlay(results):
    """Overlay product B profiles for all scenarios."""
    plt.rcParams.update({"font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle('Fed-Batch Hydrogenation — Scenario Overlay', fontsize=14, fontweight="bold")
    colours = ['steelblue', 'tomato', 'seagreen', 'darkorange', 'purple']
    for i, (name, (sol, _, _)) in enumerate(results.items()):
        c = colours[i % len(colours)]
        label = name.replace('_', ' ')
        axes[0].plot(sol.t, sol.y[1], label=label, color=c, linewidth=2)
        axes[1].plot(sol.t, sol.y[3], label=label, color=c, linewidth=2)

    axes[0].set_xlabel('Time (min)')
    axes[0].set_ylabel('B concentration (mol/L)')
    axes[0].set_title('Product B Concentration — Scenario Overlay')
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    axes[1].set_xlabel('Time (min)')
    axes[1].set_ylabel('Dissolved H2 (mol/L)')
    axes[1].set_title('Dissolved H2 — Scenario Overlay')
    axes[1].axhline(p.H2_LIMITATION_THRESHOLD, linestyle='--', color='red', alpha=0.6,
                    label=f'H2 threshold ({p.H2_LIMITATION_THRESHOLD} mol/L)')
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
