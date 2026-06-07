"""Generate technical risk assessment table for fed-batch hydrogenation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd

from src.simulate import run_simulation
from src.scenarios import run_all_scenarios
from src.utils import ensure_dirs, compute_metrics, risk_score, build_params, RESULTS_DIR


RISK_TABLE = [
    {
        'risk': 'Incomplete substrate conversion',
        'model_output': 'Final conversion of A',
        'threshold': '> 95%',
        'likely_cause': 'Insufficient batch time, low catalyst loading or feed rate too high',
        'mitigation': 'Extend batch time; reduce feed rate; increase catalyst loading',
    },
    {
        'risk': 'Hydrogen mass transfer limitation',
        'model_output': 'Time fraction with dissolved H2 below 40% of saturation (0.06 mol/L at 3 bar)',
        'threshold': '< 10% of batch time',
        'likely_cause': 'Low kLa, low H2 pressure or high feed rate consuming H2 faster than transfer',
        'mitigation': 'Increase agitation or H2 pressure; reduce feed rate; improve sparger design',
    },
    {
        'risk': 'Excessive impurity C formation',
        'model_output': 'Final impurity fraction C/(B+C)',
        'threshold': '< 5 mol%',
        'likely_cause': 'High local H2 concentration driving over-hydrogenation (k2 pathway)',
        'mitigation': 'Reduce H2 pressure; control feed rate; optimise catalyst selectivity',
    },
    {
        'risk': 'Excessive batch time',
        'model_output': 'Time to reach target conversion',
        'threshold': 'Within defined batch window',
        'likely_cause': 'Low feed concentration, low catalyst activity or mass transfer limited',
        'mitigation': 'Increase catalyst loading; increase feed concentration; improve H2 delivery',
    },
    {
        'risk': 'Scale-up sensitivity (kLa drop)',
        'model_output': 'Conversion and H2 limitation at lower kLa',
        'threshold': 'Conversion > 95% at kLa = 0.5 /min',
        'likely_cause': 'Mixing and mass transfer efficiency typically lower at pilot/manufacturing scale',
        'mitigation': 'Design with kLa safety margin; validate at pilot scale; consider semi-batch H2 dosing',
    },
]


def print_risk_table(df):
    """Print a readable risk summary to console."""
    print('\n=== Technical Risk Table ===')
    for _, row in df.iterrows():
        print(f"\nRisk: {row['risk']}")
        print(f"  Model output : {row['model_output']}")
        print(f"  Threshold    : {row['threshold']}")
        print(f"  Likely cause : {row['likely_cause']}")
        print(f"  Mitigation   : {row['mitigation']}")


def scenario_risk_summary(scenario_results):
    """Build a summary table with scenario name, metrics and risk rating."""
    rows = []
    for name, (_, metrics, risk) in scenario_results.items():
        rows.append({
            'scenario': name,
            'conversion': round(metrics['conversion'], 3),
            'impurity_fraction': round(metrics['impurity_fraction'], 4),
            'min_h2': round(metrics['min_h2'], 4),
            'time_h2_limited_pct': round(metrics['time_h2_limited_fraction'] * 100, 1),
            'risk_rating': risk,
        })
    return pd.DataFrame(rows)


if __name__ == '__main__':
    ensure_dirs()

    print('Running all scenarios for risk assessment...')
    scenario_results = run_all_scenarios()

    risk_df = pd.DataFrame(RISK_TABLE)
    path = os.path.join(RESULTS_DIR, 'risk_table.csv')
    risk_df.to_csv(path, index=False)
    print(f'Saved: {path}')
    print_risk_table(risk_df)

    summary_df = scenario_risk_summary(scenario_results)
    print('\n=== Scenario Risk Summary ===')
    print(summary_df.to_string(index=False))

    summary_path = os.path.join(RESULTS_DIR, 'scenario_risk_summary.csv')
    summary_df.to_csv(summary_path, index=False)
    print(f'Saved: {summary_path}')
