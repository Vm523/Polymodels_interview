# Fed-Batch Hydrogenation Process Model

## What I built and why

I built a Python ODE model of a fed-batch catalytic hydrogenation reactor as a technical interview project. The goal was to show how process modelling can support pharmaceutical CMC development — specifically, how you can use a relatively simple mechanistic model to do meaningful technical risk assessment before committing any lab time. I wanted to identify which parameters actually matter, what the scale-up risks are, and whether the process has a wide enough operating window to be manufacturable.

The context is ICH Q8 design space thinking: rather than just optimising a single set of conditions, I wanted to map out which combinations of operating parameters give acceptable conversion and purity — and which ones don't.

## Why fed-batch hydrogenation?

Catalytic hydrogenation is one of the most common steps in API synthesis — reducing a nitro group, saturating a double bond, removing a protecting group. In a standard batch you charge everything at once; in fed-batch you add the substrate gradually to a reactor that already contains solvent, catalyst, and hydrogen. I chose fed-batch because the control element makes it more interesting to model: you're managing hydrogen demand, exotherm, and selectivity simultaneously through the feed profile.

The engineering challenge that motivated the whole project is hydrogen mass transfer. H2 has to dissolve from the gas phase into the liquid before it can react, and that transfer rate — characterised by kLa — is the main thing that changes when you scale up. At lab scale kLa is usually fine. At manufacturing scale it can drop 3–10x because the geometry changes and you can't just increase agitation proportionally. That's one of the most common reasons a hydrogenation that looks clean on the bench fails at scale — the dissolved H2 drops, the reaction slows, and you get incomplete conversion or the selectivity shifts. I built the model specifically to quantify that risk.

## What the model does

I tracked five state variables over the batch time:

- **A** — substrate concentration (mol/L): what I'm feeding in and want to consume completely
- **B** — desired product (mol/L): the target molecule
- **C** — impurity (mol/L): over-hydrogenated side product that determines whether I hit purity spec
- **H2** — dissolved hydrogen (mol/L): the key variable for understanding mass-transfer limitation
- **V** — reactor volume (L): increases as feed is added, needed to get dilution terms right

I modelled two reactions:

```
A + H2 → B    rate = k1 × A × H2   (desired hydrogenation)
B + H2 → C    rate = k2 × B × H2   (over-hydrogenation, side reaction)
```

Both are second-order — first order in substrate, first order in dissolved H2. I used simplified Langmuir-Hinshelwood kinetics (which reduces to second-order when the catalyst surface isn't saturated), which I think is reasonable for a screening model.

I modelled hydrogen mass transfer as:

```
r_transfer = kLa × (H2_sat − H2)
```

where H2_sat comes from a simplified Henry's law (linear with headspace pressure). When the reaction is fast relative to transfer, H2 stays depleted and I'm in the mass-transfer-limited regime — which is exactly the scale-up risk I wanted to quantify.

I solved the ODEs with `scipy.integrate.solve_ivp` using the Radau solver. I chose Radau rather than RK45 because the system is stiff when kLa is high — the H2 dynamics have a much shorter timescale than the conversion dynamics, and explicit solvers take tiny steps trying to stay stable.

## Assumptions I made

I tried to be honest about where I simplified:

- **Perfectly mixed reactor.** No spatial concentration gradients. In a real large stirred tank there will be zones of varying H2 availability, particularly near the sparger.
- **Isothermal operation.** I absorbed temperature dependence into fixed rate constants. For an exothermic reaction this is a significant simplification — if cooling is imperfect, k1 and k2 would drift during the batch.
- **Simplified Henry's law.** H2_sat scales linearly with pressure. This ignores solvent effects and non-ideal gas behaviour, which matters in organic solvents.
- **Second-order kinetics.** A full Langmuir-Hinshelwood model with explicit surface coverage would be more accurate at high catalyst loadings, but for parameter sensitivity screening I think second-order captures the main behaviour.
- **No catalyst deactivation.** Catalyst activity is constant throughout. Poisoning and sintering do happen in practice, particularly with dirty feeds.
- **Constant H2 headspace pressure.** I assumed an infinite H2 reservoir. Gas-phase H2 depletion in a closed headspace would matter in a sealed system.
- **Constant feed rate for the full batch.** There's no variable feed profile. In reality, tapering the feed rate at the end to reduce over-hydrogenation is a real process lever.

## How to run

```
pip install -r requirements.txt

python src/simulate.py        # base-case simulation — plots and CSV
python src/scenarios.py       # scenario comparison and design space analysis
python src/sensitivity.py     # one-at-a-time parameter sweeps
python src/risk_assessment.py # risk scoring across all scenarios

pytest tests -q               # 16 unit tests
```

Plots save to `results/figures/` and data to `results/`.

## What I found

The base case gives around 96% conversion with about 5% impurity — Medium risk. That's a reasonable starting point but not something I'd be comfortable taking straight to manufacturing.

The more important results came from the scenario analysis. When I dropped kLa to 0.2 /min — simulating a scale-up where gas dispersion is worse — conversion fell to 87.6% and the process was H2-limited for 100% of the batch. That's the High risk outcome and the one that most directly maps to a real scale-up failure. The sensitivity analysis confirmed that kLa is the dominant parameter, more so than feed rate or catalyst loading.

The high catalyst scenario was also telling: conversion went up to 97.7%, but impurity climbed to 26.6%. The faster reaction consumed A quickly, so the B/A ratio in the reactor rose earlier in the batch and the over-hydrogenation side reaction dominated. Same risk rating as the low kLa case but for a completely different reason — which is why I thought it was important to track both conversion and selectivity simultaneously.

I also added a design space analysis — a 2D grid of kLa versus feed rate showing which combinations give acceptable performance. The acceptable operating region shrinks rapidly below kLa ≈ 0.4 /min, which is the key number for a scale-up engineer to care about.

## How this supports CMC decisions

The main value I see in this kind of model is prioritisation. Before going into the lab, you want to know which parameters are most likely to cause a failure — not just optimistically, but with some quantitative backing. The model lets me say "kLa is the critical parameter, here's what happens below 0.4 /min, here's the acceptable operating window" — and that directly informs what measurements to take, what tolerances to put on operating parameters, and where to focus scale-up characterisation.

It maps naturally to ICH Q8 design space justification: I can show a region of parameter space where the CQAs are met, and explain what drives the boundaries of that region.

It's not a substitute for experimental data — I need lab runs to validate k1, k2, and kLa for the actual substrate — but it's faster than 50 experiments and it structures the conversation about risk.

## Limitations and what I'd do next

The biggest gaps are:

- **No temperature dynamics.** Adding an Arrhenius equation and a heat balance would let me explore the cooling capacity versus selectivity tradeoff, which is important for a real exothermic step.
- **No Monte Carlo analysis.** My one-at-a-time sweeps miss parameter interactions. Drawing k1, k2, and kLa from distributions and propagating uncertainty would give a probability of failure rather than a point estimate.
- **kLa not linked to reactor geometry.** If I used a van't Riet correlation to predict kLa from P/V and superficial gas velocity, the scale-up risk assessment would be much more concrete — I could actually predict kLa at pilot scale from the agitator design.
- **No experimental validation.** The rate constants are estimates. Fitting to lab concentration-time data would tell me whether the model is capturing the real chemistry.
