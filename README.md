# Fed-Batch Hydrogenation Process Model

This project is a Python model of a fed-batch catalytic hydrogenation reaction. I built it as part of a technical exercise to show how process modelling can support pharmaceutical CMC risk assessment.

## What is fed-batch hydrogenation?

In a fed-batch hydrogenation, a substrate is gradually added to a reactor containing solvent, catalyst and hydrogen gas. The hydrogen dissolves from the gas phase into the liquid and reacts with the substrate to form the desired product. Doing it fed-batch rather than batch lets you control the hydrogen demand and keep the process safer.

This kind of step is common in API synthesis — for example reducing a nitro group or a double bond. Getting it right matters because incomplete conversion or too much impurity can cause downstream purification problems and regulatory headaches.

## What the model does

The model tracks five state variables over time:
- A: substrate concentration (mol/L)
- B: desired product (mol/L)
- C: impurity from over-hydrogenation (mol/L)
- H2: dissolved hydrogen (mol/L)
- V: reactor volume (L)

Two reactions are modelled:
- A + H2 → B (desired, rate constant k1)
- B + H2 → C (side reaction, rate constant k2)

Hydrogen mass transfer is modelled as: kLa × (H2_sat − H2), where H2_sat comes from a simplified Henry's law (linear with pressure).

The fed-batch dilution terms are included so volume changes affect all concentrations as the substrate feed is added.

## Assumptions

- Perfectly mixed reactor (no spatial gradients)
- Isothermal operation (temperature effect absorbed into rate constants)
- Ideal Henry's law for H2 solubility
- Second-order kinetics (first order in both A and H2, first order in B and H2 for side reaction)
- Catalyst deactivation neglected
- No mass transfer resistance for liquid-phase species other than H2

## How to run

Install dependencies:

    pip install -r requirements.txt

Run the base-case simulation:

    python src/simulate.py

Run scenario comparison:

    python src/scenarios.py

Run sensitivity analysis:

    python src/sensitivity.py

Run risk assessment:

    python src/risk_assessment.py

Run tests:

    pytest tests -q

Outputs are saved to results/figures/ (plots) and results/ (CSV files).

## How the model supports risk assessment

The model lets you ask "what happens if X goes wrong?" — for example, if the kLa drops at scale or if the feed rate is higher than expected. By running scenarios and sensitivity sweeps, you can identify which parameters the process is most sensitive to before going into the lab. That informs where to focus experimental work and what operating ranges to put in the process control strategy.

## Limitations and possible improvements

- Real hydrogenation kinetics are more complex (Langmuir-Hinshelwood, catalyst surface coverage)
- Temperature effects should really be in there — an Arrhenius term for k1 and k2
- The model doesn't account for gas-phase H2 depletion as it's consumed
- Catalyst deactivation over time is ignored
- A proper uncertainty analysis (Monte Carlo) would be more rigorous than one-at-a-time sensitivity
