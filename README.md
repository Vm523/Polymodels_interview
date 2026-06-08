# Fed-Batch Hydrogenation Process Model

## What this is

This is a Python-based ODE model of a fed-batch catalytic hydrogenation reactor, built as part of a technical interview project demonstrating how process modelling fits into pharmaceutical CMC development. The motivation was to show that you can use relatively simple mechanistic models to do meaningful technical risk assessment — identifying critical process parameters and scale-up concerns before you commit lab time. It's the kind of analysis that would sit naturally in an early-phase CMC package or a design space justification under ICH Q8.

## What is fed-batch hydrogenation?

Catalytic hydrogenation is one of the most common transformations in API synthesis — reducing a nitro group, saturating a double bond, removing a protecting group. In a batch process you charge everything at once; in fed-batch you add the substrate gradually to a reactor that already contains solvent, catalyst, and hydrogen. The reason to go fed-batch is control: you limit the instantaneous substrate concentration, which helps manage hydrogen demand, reaction exotherm, and selectivity. For a reduction where over-hydrogenation is a real impurity pathway, keeping the substrate lean can meaningfully improve the product ratio.

The interesting engineering challenge is hydrogen mass transfer. H2 is a gas dissolving into a liquid, and its transfer rate is governed by kLa (the volumetric mass transfer coefficient). At lab scale, kLa is usually not limiting. At pilot or manufacturing scale, the mass transfer rate per unit volume tends to drop because the geometry changes and you can't just scale up agitator speed proportionally. This is one of the most common reasons a hydrogenation that looks clean on the bench performs poorly at scale — the liquid-phase H2 concentration drops, the reaction slows, and you either get incomplete conversion or the selectivity shifts. The model is specifically designed to probe this.

## Model description

The system is described by five state variables integrated over the batch time:

- **A** — substrate concentration (mol/L). This is what you're adding in the feed and what you want to consume completely.
- **B** — desired product concentration (mol/L). The target molecule; you want this as high as possible.
- **C** — impurity concentration (mol/L). The over-hydrogenated side product. Tracking this is important because it determines whether you'll hit purity spec.
- **H2** — dissolved hydrogen concentration (mol/L). The key variable for understanding mass-transfer limitations. When this is low, the reaction is H2-starved.
- **V** — reactor volume (L). Volume increases as feed is added, so you need to carry it as a state to correctly compute dilution of all other species.

Two reactions are modelled:

```
A + H2 → B    rate = k1 * A * H2   (desired hydrogenation)
B + H2 → C    rate = k2 * B * H2   (over-hydrogenation, side reaction)
```

Both are second-order (first order in substrate, first order in dissolved H2). This is a simplification — real heterogeneous hydrogenation kinetics are usually Langmuir-Hinshelwood, with catalyst surface coverage playing a role — but for the purpose of parameter sensitivity and risk screening it captures the essential behaviour.

Hydrogen mass transfer into the liquid is modelled as:

```
r_transfer = kLa * (H2_sat - H2)
```

where H2_sat is the saturation concentration at the reactor headspace pressure, calculated via a simplified Henry's law (linear relationship with partial pressure). The transfer term drives dissolved H2 toward equilibrium; when the reaction is fast relative to transfer, H2 stays depleted and you're in the mass-transfer-limited regime.

Fed-batch dilution terms are included throughout — as volume increases, all concentrations are diluted proportionally, which is important for getting the timing of the selectivity right. The substrate feed is modelled as a constant volumetric flow rate running for the full batch duration.

The ODEs are solved using `scipy.integrate.solve_ivp` with the Radau solver. Radau is an implicit Runge-Kutta method suited to stiff systems, which this one becomes when kLa is high relative to the reaction rate constants — the H2 dynamics then have a very short timescale compared to the conversion dynamics, and explicit solvers struggle.

## Assumptions

There are several simplifying assumptions worth being honest about:

- **Perfectly mixed reactor.** No spatial gradients in concentration. In reality, a large stirred tank will have zones of varying H2 availability, especially near the gas sparger versus away from it.
- **Isothermal operation.** Temperature is assumed constant throughout. This means any temperature dependence of k1 and k2 is absorbed into fixed constants. If the reaction is significantly exothermic and cooling is imperfect, the real rate constants would drift during the batch.
- **Simplified Henry's law for H2 solubility.** H2_sat is a linear function of headspace pressure. This is reasonable at moderate pressures but ignores solvent effects and non-ideal gas behaviour.
- **Second-order kinetics.** As noted above, real heterogeneous hydrogenation typically follows Langmuir-Hinshelwood kinetics with explicit catalyst surface terms. The second-order approximation works reasonably well when the catalyst is not saturated, but it will overestimate the rate at high H2.
- **No catalyst deactivation.** Catalyst activity is assumed constant throughout the batch. In practice, poisoning and sintering do happen, particularly over longer batches or with feeds that contain trace impurities.
- **Constant H2 headspace pressure.** The model assumes an infinite H2 reservoir at fixed pressure. Gas-phase H2 depletion is not tracked, which would matter in a closed system with limited headspace volume.
- **Feed runs continuously for the full batch time.** The substrate feed rate is constant from t=0 to t=t_end. There's no provision for variable feed profiles, which is a real tool in optimising selectivity.

## How to run

Install the dependencies:

```
pip install -r requirements.txt
```

Then you can run each component separately:

```
python src/simulate.py        # base-case simulation, generates plots and CSV
python src/scenarios.py       # compare base case vs. low kLa and high catalyst scenarios
python src/sensitivity.py     # one-at-a-time parameter sensitivity sweeps
python src/risk_assessment.py # risk scoring across all scenarios
pytest tests -q               # run the unit tests
```

Plots are saved to `results/figures/` and CSV outputs to `results/`.

## Key results

The base case gives around 96% conversion with about 5% impurity and comes out as Medium risk — a reasonable starting point that you'd want to improve before going into manufacturing.

The more interesting results come from the scenarios. The low kLa case (halving the mass transfer coefficient to simulate a scale-up with worse gas dispersion) drops conversion to 87.6%, with 100% of the process flagged as H2-limited. This is the high-risk outcome and the one that corresponds most directly to a real scale-up failure mode. The sensitivity analysis confirms that kLa is the most influential parameter in the model — more so than the feed rate or the rate constants — which points to agitation and sparger design as the primary engineering controls to get right.

The high catalyst loading scenario is also instructive: conversion goes up to 97.7%, but impurity climbs to 26.6% because the faster reaction consumes dissolved H2 more aggressively and drives the selectivity toward over-hydrogenation. It scores High risk for a different reason than the low kLa case, which is a good example of why you need to look at both conversion and purity together.

## How this supports risk assessment

The framing here maps to CMC and ICH Q8 design space thinking. Before you go into the lab, you want to know which process parameters are most likely to cause a failure — not just optimistically, but quantitatively. By running the model across a parameter space (kLa, feed rate, catalyst loading, rate constants), you get a structured picture of the process sensitivity that can directly inform the control strategy. It helps prioritise what to measure, what tolerances to put on operating parameters, and where to focus scale-up characterisation work.

It's not a substitute for experimental data, but it's much faster to run 50 model scenarios than 50 lab experiments, and if the model is honest about its assumptions, the results are genuinely useful for technical risk conversations.

## Limitations

The main limitations to be aware of:

- **Kinetics are simplified.** Langmuir-Hinshelwood kinetics with explicit catalyst surface terms would be more physically accurate, particularly at high catalyst loadings where surface saturation matters.
- **No temperature dependence.** There's no Arrhenius equation for k1 and k2. For a real exothermic hydrogenation, temperature excursions during the batch could meaningfully change the selectivity.
- **Gas phase H2 depletion not tracked.** In a sealed system or one with limited H2 supply, headspace pressure would drop as H2 is consumed. The model assumes it stays constant.
- **Catalyst deactivation is ignored.** This is probably fine for a short batch with clean feed, but for longer processes or feeds with potential poisons it's a real gap.
- **No spatial mixing effects.** The perfectly-mixed assumption means the model can't capture the concentration gradients you actually see in large stirred tanks.

## Possible improvements

Four improvements that would make this genuinely more useful:

1. **Arrhenius temperature dependence.** Add `k1(T) = A1 * exp(-Ea1/RT)` and similarly for k2, and include an energy balance. This would let you model the interplay between cooling capacity and selectivity.
2. **Monte Carlo sensitivity analysis.** The current one-at-a-time sweeps are a useful starting point but don't capture parameter interactions. Sampling from distributions over all uncertain parameters simultaneously would give a more complete picture of the process risk envelope.
3. **Correlate kLa to P/V for scale-up prediction.** There are empirical correlations (e.g., van't Riet) that relate kLa to power input per unit volume and superficial gas velocity. Putting that in would let you predict kLa at pilot scale from agitator geometry and power draw, making the scale-up risk assessment much more concrete.
4. **Validate against lab data.** The model parameters are currently literature-based estimates. Fitting k1, k2, and kLa to actual concentration-time profiles from a lab run would tell you whether the model is capturing the real chemistry and give you more confidence in the scale-up predictions.
