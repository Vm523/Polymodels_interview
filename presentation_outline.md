# Presentation Outline — Fed-Batch Hydrogenation Modelling for Pharma Process Risk Assessment

**Duration:** 15 minutes  
**Role:** Process Modelling Engineer Internship

---

## Slide 1 — Aim and Problem Statement (1 min)

**Key points:**
- Goal: develop a process model for fed-batch hydrogenation and use it for technical risk assessment
- Context: pharmaceutical CMC — need to demonstrate that a synthetic step meets quality targets before scaling up
- Why modelling? Saves experimental time, identifies risky conditions early, supports regulatory strategy

**Speaker notes:**
Open by framing the problem. In pharma process development you can't afford to discover a problem at pilot scale — the cost and timeline impact is too high. Modelling lets you explore scenarios computationally first.

---

## Slide 2 — What is Fed-Batch Hydrogenation? (1.5 min)

**Key points:**
- Substrate added gradually to reactor containing solvent, catalyst and H2
- H2 dissolves from gas phase (mass transfer limited) and reacts at catalyst surface
- Common in API synthesis: nitro reduction, double bond saturation
- Fed-batch mode: controls H2 demand, avoids exotherms, safer than full batch

**Speaker notes:**
Keep it brief. The audience likely knows the chemistry. Emphasise the fed-batch control element — why not just charge everything at once? Because you get better selectivity and safety control by dosing the substrate slowly.

---

## Slide 3 — Key Technical Risks (1 min)

**Key points:**
- Incomplete conversion of substrate A → regulatory failure
- H2 mass transfer limitation → starved reaction, slow batch
- Over-hydrogenation (impurity C) → purity specification breach
- Excessive batch time → throughput and cost impact
- Scale-up: kLa drops at larger scale → all the above get worse

**Speaker notes:**
This is the risk register the model is built to interrogate. Each risk maps directly to a model output. This slide sets up why the model is structured the way it is.

---

## Slide 4 — Model Structure and Assumptions (2 min)

**Key points:**
- Five state variables: A, B, C, H2, V
- Reactions: A + H2 → B (desired), B + H2 → C (side)
- H2 mass transfer: kLa × (H2_sat − H2)
- H2_sat from simplified Henry's law: H2_sat = H2_sat_base × P
- Fed-batch dilution terms in every species ODE
- Solved with scipy solve_ivp (Radau stiff solver)

**Key assumptions:**
- Perfectly mixed, isothermal
- Second-order kinetics (first order in substrate, first order in H2)
- No catalyst deactivation
- Ideal Henry's law

**Speaker notes:**
Walk through the ODE structure. Mention that Radau is appropriate for stiff problems — this system can be stiff when kLa is large and reactions are fast. Highlight the assumption list honestly — knowing where the model breaks down is part of good engineering judgement.

---

## Slide 5 — Model Inputs and Outputs (1 min)

**Inputs:**
- Feed rate, feed concentration
- H2 pressure (sets H2_sat)
- kLa (mass transfer coefficient)
- k1, k2 (reaction rate constants)
- Initial volume, batch time

**Outputs:**
- Concentration profiles: A, B, C, H2
- Final conversion, yield, selectivity
- Impurity fraction
- Minimum dissolved H2
- Time fraction under H2 limitation
- Risk rating: Low / Medium / High

**Speaker notes:**
Short slide. Just make clear what goes in and what comes out. Emphasise that the risk rating is derived from model outputs against engineering thresholds.

---

## Slide 6 — Key Equations (1.5 min)

**Key points:**

Reaction rates:
- r1 = k1 × A × H2
- r2 = k2 × B × H2

Mass balance (fed-batch, for species A):
- dA/dt = (F × CA_feed / V) − (F/V) × A − r1

H2 mass transfer:
- dH2/dt = kLa × (H2_sat − H2) − r1 − r2 − (F/V) × H2

H2 saturation (Henry's law):
- H2_sat = H2_sat_base × P

Volume:
- dV/dt = F

**Speaker notes:**
Don't read every equation. Pick one (e.g. the H2 balance) and walk through each term: transfer in, consumed by reaction 1, consumed by reaction 2, diluted by feed. That shows you understand the physics, not just that you can write ODEs.

---

## Slide 7 — Base-Case Simulation Results (2 min)

**Show plot:** concentration_profiles_base.png

**Key points:**
- Substrate A is consumed progressively as feed adds it and reaction depletes it
- Product B builds up and then levels off
- Impurity C stays low — k2 is small relative to k1
- Dissolved H2 reaches a quasi-steady state — mass transfer and consumption balance
- Final conversion ~95%, impurity fraction ~2–3%

**Speaker notes:**
Point out the quasi-steady H2 profile. This is what you want — H2 is not zero (not mass transfer limited) but not excessively high (which would drive over-hydrogenation). The base case is designed to be the "good" operating point.

---

## Slide 8 — Scenario Comparison (2 min)

**Show plot:** scenario_comparison.png

**Scenarios:**
1. Base case — balanced operation
2. High feed rate — H2 can't keep up, conversion drops, H2 limitation increases
3. Low H2 transfer (low kLa) — worst case for H2 limitation, conversion at risk
4. High catalyst loading — faster reaction, but impurity rises with over-hydrogenation
5. High H2 pressure — more H2 available, but impurity risk if k2 is significant

**Key insight:**
- Low kLa is the riskiest single change — it affects both conversion and H2 limitation
- High feed rate without adjusting H2 delivery also elevates risk

**Speaker notes:**
The scenario comparison is what you'd present to a process development team to justify operating ranges. You can say: "our process is robust to changes in feed rate as long as kLa stays above X."

---

## Slide 9 — Sensitivity Analysis (1.5 min)

**Show plot:** sensitivity_analysis.png

**Key points:**
- kLa has the largest impact on H2 limitation and conversion — critical parameter
- H2 pressure: increasing it reduces H2 limitation but risks higher impurity
- Feed rate: strong effect on H2 limitation; moderate effect on conversion
- k1 (reaction rate): conversion improves with higher k1 but so does impurity via k2

**Key insight:**
- kLa is the parameter the process is most sensitive to — this is the scale-up risk

**Speaker notes:**
One-at-a-time sensitivity is a starting point. A real assessment would use Monte Carlo to handle parameter correlations and uncertainty. But for a 15-minute presentation this is the right level of detail.

---

## Slide 10 — Risk Assessment Table (1 min)

**Show table with columns:** Risk | Model output | Threshold | Likely cause | Mitigation

| Risk | Threshold | Rating |
|------|-----------|--------|
| Incomplete conversion | > 95% | Medium |
| H2 mass transfer limitation | < 10% batch time | Medium |
| Impurity formation | < 5 mol% | Low |
| Excessive batch time | Within window | Low |
| Scale-up kLa sensitivity | Conv > 95% at kLa=0.5 | High |

**Speaker notes:**
This table is what you'd put in a process risk assessment document. It links each engineering risk to a quantitative threshold derived from the model. The scale-up kLa risk is rated High because the model shows conversion falling below target at kLa < 0.5 /min.

---

## Slide 11 — How This Supports CMC Decisions (1 min)

**Key points:**
- Helps define the design space: which combinations of feed rate and kLa give acceptable conversion and impurity
- Identifies critical process parameters (CPPs): kLa is the highest sensitivity parameter
- Supports risk-based justification for process controls in regulatory submissions
- Reduces experimental workload — screen conditions in silico first

**Speaker notes:**
Frame this in terms of ICH Q8/Q10 language if you know it. The model doesn't replace experiments but it helps you run the right experiments. For a CMC submission you need to show you understand what controls the critical quality attributes — this model starts that conversation.

---

## Slide 12 — Limitations and Next Steps (0.5 min)

**Limitations:**
- Isothermal assumption — temperature effects on kinetics not modelled
- Simplified Henry's law — real H2 solubility depends on solvent and temperature
- Ideal mixing — no spatial gradients or dead zones
- No catalyst deactivation

**Next steps:**
- Add Arrhenius temperature dependence to k1 and k2
- Replace one-at-a-time with Monte Carlo sensitivity
- Validate against lab-scale experimental data
- Extend to pilot scale with correlated kLa model

**Speaker notes:**
Finishing with limitations shows engineering maturity. You're not over-selling the model. Mention that the most valuable next step is experimental validation — the model tells you where to look, experiments tell you if you were right.

---

*End of presentation*
