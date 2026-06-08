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
        'severity': 'Critical',
        'model_output': 'Final conversion of A',
        'threshold': '> 95%',
        'likely_cause': 'Insufficient batch time, low catalyst loading, feed rate too high, or H2 mass transfer limited',
        'pharma_impact': 'Unreacted substrate A carries through to downstream purification, increasing impurity load and potentially causing CQA failures at drug substance release',
        'mitigation': 'Extend batch time; reduce feed rate; increase catalyst loading; verify H2 supply is not limiting',
    },
    {
        'risk': 'Hydrogen mass transfer limitation',
        'severity': 'High',
        'model_output': 'Time fraction with dissolved H2 below 40% of saturation (0.06 mol/L at 3 bar)',
        'threshold': '< 10% of batch time',
        'likely_cause': 'Low kLa due to insufficient agitation, sparger fouling, or scale-up — kLa typically drops 3-10x between lab and manufacturing scale',
        'pharma_impact': 'H2-starved conditions slow the reaction, extend batch time, and increase process variability — a major scale-up risk that must be characterised before tech transfer',
        'mitigation': 'Increase agitation speed or H2 pressure; improve sparger design; characterise kLa at each scale; set minimum agitation requirement in process control strategy',
    },
    {
        'risk': 'Excessive impurity C formation (over-hydrogenation)',
        'severity': 'High',
        'model_output': 'Final impurity fraction C/(B+C)',
        'threshold': '< 5 mol%',
        'likely_cause': 'Product B over-hydrogenated when H2 availability is high and substrate A is nearly depleted — the B/A ratio rises late in the batch, making the side reaction dominant',
        'pharma_impact': 'Impurity C may be a genotoxic or toxic degradant requiring ICH M7 assessment; exceeding the specification threshold triggers batch failure and costly re-purification or rejection',
        'mitigation': 'Monitor conversion in-line; stop batch at optimal endpoint; reduce H2 pressure in later stages; select more selective catalyst (lower k2/k1 ratio)',
    },
    {
        'risk': 'Excessive batch time',
        'severity': 'Medium',
        'model_output': 'Time to reach 95% conversion (model KPI)',
        'threshold': 'Within defined manufacturing window',
        'likely_cause': 'Low catalyst activity, H2 mass transfer limited, or feed rate too low relative to reaction rate',
        'pharma_impact': 'Long batch cycles reduce manufacturing throughput, increase solvent consumption and energy costs, and may cause catalyst deactivation or product degradation',
        'mitigation': 'Optimise feed rate and catalyst loading together; confirm reaction is not H2-limited; consider higher H2 pressure to accelerate kinetics',
    },
    {
        'risk': 'Scale-up sensitivity — kLa reduction',
        'severity': 'Critical',
        'model_output': 'Conversion and H2 limitation fraction at kLa = 0.2 /min (pilot/manufacturing estimate)',
        'threshold': 'Conversion > 95% maintained at reduced kLa',
        'likely_cause': 'Gas-liquid mass transfer efficiency (kLa) is geometry- and scale-dependent; it typically decreases on scale-up due to larger bubble size, lower P/V ratio, and different mixing patterns',
        'pharma_impact': 'A process that works at lab scale (kLa ~ 0.8/min) may fail at manufacturing scale (kLa ~ 0.1-0.3/min), causing conversion and purity failures — a primary source of tech transfer risk',
        'mitigation': 'Characterise kLa at each scale; design process with kLa safety margin; validate at pilot scale before manufacturing; consider semi-batch H2 dosing strategy',
    },
    {
        'risk': 'Narrow operating window (poor robustness)',
        'severity': 'Medium',
        'model_output': 'Design space analysis — acceptable kLa and feed rate combinations',
        'threshold': 'Operating window should tolerate ±20% variation in feed rate and ±30% variation in kLa',
        'likely_cause': 'Process parameters near the edge of the acceptable space; small deviations in feed pump calibration or agitator speed cause specification failures',
        'pharma_impact': 'Narrow operating windows increase process risk during commercial manufacturing where equipment variability is unavoidable; requires tighter process controls and more frequent out-of-specification investigations',
        'mitigation': 'Use sensitivity analysis and design space plots to identify robust operating region; set process parameters in the centre of the acceptable window, not at the edge',
    },
]


def print_risk_table(df):
    """Print a readable risk summary to console."""
    print('\n=== Technical Risk Table ===')
    for _, row in df.iterrows():
        print(f"\nRisk: {row['risk']}")
        print(f"  Severity     : {row['severity']}")
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
            'time_to_target_min': round(metrics.get('time_to_target_conversion', 120), 1),
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
