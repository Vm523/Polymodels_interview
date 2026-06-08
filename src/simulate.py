"""Run base-case fed-batch hydrogenation simulation and save outputs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

from src.model import odes
from src.utils import ensure_dirs, compute_metrics, risk_score, build_params, FIGURES_DIR, RESULTS_DIR
import src.parameters as p


def run_simulation(params=None):
    """Run the ODE model and return the solution object."""
    if params is None:
        params = build_params()

    y0 = [p.A0, p.B0, p.C0, p.H2_0, params['v0']]
    t_span = (0.0, params['t_end'])
    t_eval = np.linspace(0.0, params['t_end'], params['n_eval'])

    sol = solve_ivp(
        odes,
        t_span,
        y0,
        args=(params,),
        method='Radau',
        t_eval=t_eval,
        rtol=1e-6,
        atol=1e-8,
    )
    return sol


def plot_concentrations(sol, params, label='base', save=True):
    """Plot concentration profiles and dissolved H2 over time."""
    plt.rcParams.update({'font.size': 11, 'axes.titlesize': 12, 'axes.labelsize': 11})
    t = sol.t
    A, B, C, H2, V = sol.y

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle(f'Fed-Batch Hydrogenation Simulation — {label.replace("_"," ").title()}', fontsize=14, fontweight='bold', y=1.01)

    axes[0, 0].plot(t, A, label='A (substrate)', color='royalblue', linewidth=2, marker=None)
    axes[0, 0].plot(t, B, label='B (product)', color='seagreen', linewidth=2, marker=None)
    axes[0, 0].plot(t, C, label='C (impurity)', color='tomato', linewidth=2, marker=None)
    axes[0, 0].set_xlabel('Time (min)')
    axes[0, 0].set_ylabel('Concentration (mol/L)')
    axes[0, 0].set_title('Species Concentrations')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(t, H2, color='#E07B39', linewidth=2)
    axes[0, 1].axhline(p.H2_LIMITATION_THRESHOLD, linestyle='--', color='red', alpha=0.6, label=f'H2 limit ({p.H2_LIMITATION_THRESHOLD} mol/L)')
    axes[0, 1].set_xlabel('Time (min)')
    axes[0, 1].set_ylabel('Dissolved H2 (mol/L)')
    axes[0, 1].set_title('Dissolved Hydrogen')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    total_a_fed_cumulative = params['feed_rate'] * params['feed_conc_a'] * t
    moles_a_remaining = A * V
    conv = 1.0 - moles_a_remaining / (total_a_fed_cumulative + 1e-12)
    conv = np.clip(conv, 0, 1)

    total_prod = (B + C) * V
    impurity = (C * V) / (total_prod + 1e-12)

    axes[1, 0].plot(t, conv, color='steelblue', linewidth=2)
    axes[1, 0].axhline(p.CONVERSION_TARGET, linestyle='--', color='green', alpha=0.6, label=f'Target ({p.CONVERSION_TARGET*100:.0f}%)')
    axes[1, 0].set_xlabel('Time (min)')
    axes[1, 0].set_ylabel('Conversion (–)')
    axes[1, 0].set_title('Substrate Conversion')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(0, 1.05)

    axes[1, 1].plot(t, impurity, color='firebrick', linewidth=2)
    axes[1, 1].axhline(p.IMPURITY_THRESHOLD, linestyle='--', color='orange', alpha=0.8, label=f'Threshold ({p.IMPURITY_THRESHOLD*100:.0f} mol%)')
    axes[1, 1].set_xlabel('Time (min)')
    axes[1, 1].set_ylabel('Impurity C/(B+C) (–)')
    axes[1, 1].set_title('Impurity Fraction')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    if save:
        path = os.path.join(FIGURES_DIR, f'concentration_profiles_{label}.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        print(f'Saved: {path}')
    plt.close()


def save_timeseries(sol, label='base'):
    """Save time-series data as CSV."""
    t = sol.t
    A, B, C, H2, V = sol.y
    df = pd.DataFrame({'time_min': t, 'A_conc_mol_per_L': A, 'B_conc_mol_per_L': B,
                        'C_conc_mol_per_L': C, 'H2_conc_mol_per_L': H2, 'volume_L': V})
    path = os.path.join(RESULTS_DIR, f'timeseries_{label}.csv')
    df.to_csv(path, index=False)
    print(f'Saved: {path}')


if __name__ == '__main__':
    ensure_dirs()
    params = build_params()
    print('Running base-case simulation...')
    sol = run_simulation(params)
    plot_concentrations(sol, params, label='base')
    save_timeseries(sol, label='base')
    metrics = compute_metrics(sol, params)
    risk = risk_score(metrics, params)
    print('\nBase-case metrics:')
    for k, v in metrics.items():
        print(f'  {k}: {v:.4f}')
    print(f'  Risk rating: {risk}')
