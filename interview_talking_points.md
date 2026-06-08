# Interview Talking Points

## 1. Two-Minute Project Summary

I built a Python-based process model for a fed-batch hydrogenation reaction in a pharmaceutical context. The motivation was CMC technical risk assessment — understanding what could go wrong before you invest in lab or pilot scale experiments. The model solves a system of ODEs describing substrate conversion, product formation, impurity generation, and dissolved hydrogen dynamics simultaneously. The key finding was that gas-liquid mass transfer — characterised by kLa — is the dominant scale-up risk: the process performs well at lab scale where kLa is high, but below a critical threshold of around 0.22/min the reactor becomes permanently H2-starved and conversion drops significantly. That insight directly informs where to focus experimental effort and what process controls to justify in a regulatory submission.

---

## 2. Why Fed-Batch Hydrogenation?

- **Controlled substrate addition reduces peak H2 demand.** Adding substrate continuously rather than all at once keeps the instantaneous reaction rate lower, which means less H2 is consumed per unit time and the mass transfer system is less stressed.
- **Better temperature control.** Hydrogenations are exothermic. Spreading the substrate addition over the batch reduces the heat release rate, lowering the risk of a runaway temperature excursion.
- **Improved selectivity by controlling concentration driving forces.** Keeping substrate concentration low relative to product concentration can suppress secondary reactions (over-hydrogenation), improving yield of the desired product.
- **Safer operation.** Less substrate in the reactor at any moment means less H2 dissolved and less energy stored in the system — an important consideration for high-pressure gas-phase reactions in a pharmaceutical manufacturing environment.

---

## 3. Why H2 Mass Transfer Matters

H2 is a gas. Before it can participate in the reaction it must dissolve from the gas phase into the liquid phase where the substrate and catalyst are. This gas-to-liquid transfer is not instantaneous — it is governed by a rate constant called kLa (volumetric mass transfer coefficient, units: 1/min). The driving force is the difference between the equilibrium dissolved H2 concentration (set by pressure via Henry's law) and the actual dissolved concentration.

At lab scale, with good agitation and small reactor geometry, kLa is typically 0.5–2/min. At manufacturing scale, the surface-area-to-volume ratio drops and mixing is less efficient, so kLa commonly falls to 0.1–0.3/min.

The model shows a critical behaviour: below approximately kLa = 0.22/min at base conditions, H2 consumption by the reaction outpaces H2 supply by mass transfer. Dissolved H2 approaches zero and stays there for the entire batch — permanent H2-starvation. This is why kLa is identified as the number-one scale-up risk parameter and the variable that most warrants experimental characterisation before tech transfer.

---

## 4. Main Technical Risks (with model evidence)

1. **Incomplete conversion.** The low kLa scenario (kLa = 0.2/min) gives only 87.6% conversion against a nominal target of ~95%, directly demonstrating that a plausible scale-up kLa value puts the process out of specification.
2. **H2 mass transfer limitation.** At kLa = 0.2/min, dissolved H2 is at or near zero for 100% of the batch time — the reaction is permanently supply-limited rather than kinetically limited, a qualitatively different and more serious operating regime.
3. **Over-hydrogenation impurity.** The high catalyst scenario (k1 = 3.0, k2 = 0.05) produces 26.6% impurity — more than five times the base case level — because faster kinetics deplete substrate rapidly, increasing the product-to-substrate ratio and accelerating the secondary reaction.
4. **Narrow operating window.** The design space sensitivity plot shows that the acceptable kLa / feed rate operating region shrinks rapidly below kLa = 0.4/min, meaning small deviations from the design point carry disproportionate quality risk.
5. **Scale-up risk.** The same process that delivers ~95.7% conversion and ~5.2% impurity at lab scale may fail both metrics at pilot or manufacturing scale solely due to the reduction in kLa — a risk that would not be obvious without a model.

---

## 5. What the Sensitivity Analysis Shows

- **kLa:** The most sensitive parameter in the model. A decrease from 0.8 to 0.2/min — a factor of four, which is realistic across scales — drops conversion from 95.7% to 87.6% and switches the system from kinetically limited to permanently mass-transfer limited. No other single parameter produces this magnitude of effect.
- **Feed rate:** Moderate effect. Higher feed rates increase the instantaneous H2 demand early in the batch, temporarily stressing H2 supply and increasing the fraction of H2-limited time. However, above a certain kLa the system recovers and the final conversion is comparable to base case (95.6% at high feed rate).
- **H2 pressure:** Increasing pressure to 6 bar raises equilibrium dissolved H2, improving conversion to ~98%. However, it also elevates dissolved H2 throughout the batch, which accelerates the secondary reaction — impurity rises to 11.4% compared to 5.2% at base conditions. Pressure is not a free lever.
- **k1 (catalyst activity):** Higher catalyst activity (k1 = 3.0) improves conversion to 97.7% but impurity rises disproportionately to 26.6%. This is because the selectivity-determining ratio is k2/k1 — as both rate constants are increased together, the secondary reaction accelerates faster relative to the primary reaction than the simple numbers suggest.

---

## 6. Model Limitations (be honest — interviewers respect this)

1. **Isothermal assumption.** The model holds temperature constant throughout the batch. In reality, heat release from the exothermic reaction changes temperature, which affects both k1 and k2 through Arrhenius dependence. A temperature rise of even 5–10°C could meaningfully alter selectivity.
2. **Simplified Henry's law.** The model uses a fixed H2 solubility constant. Real H2 solubility in pharmaceutical solvents depends non-linearly on temperature, pressure, and solvent composition — particularly important if the solvent changes during the batch.
3. **No catalyst deactivation.** The model assumes constant catalyst activity throughout. In practice, palladium and other hydrogenation catalysts can be poisoned by sulfur-containing impurities or lose surface area over time, reducing effective k1 mid-batch.
4. **Perfect mixing assumed.** The model is a well-mixed CSTR-type description with no spatial gradients. Real reactors have dead zones, impeller-driven concentration profiles, and gas hold-up distributions that the model cannot capture.
5. **Simplified kinetics.** The model uses empirical second-order kinetics. Real heterogeneous hydrogenation follows a Langmuir-Hinshelwood mechanism with surface adsorption steps, competitive inhibition, and explicit catalyst site terms — especially relevant at high substrate concentrations.

---

## 7. How the Model Supports CMC Decisions

The model provides a structured, quantitative basis for identifying critical process parameters (CPPs) before any experimental work begins — in this case flagging kLa and catalyst loading as the variables most likely to affect quality. This aligns directly with ICH Q8 pharmaceutical development thinking: the design space plot generated by the model is a visual representation of acceptable kLa / feed rate combinations, which is exactly the kind of evidence regulators expect to support a defined operating space. Quantifying scale-up risk ahead of tech transfer to pilot plant means the development team can allocate experiments where they matter most rather than discovering failures at scale. It also supports risk-based justification for process analytical technology (PAT) controls — for example, recommending real-time dissolved H2 monitoring as a critical control because the model demonstrates the process is sensitive to it. Ultimately, models like this reduce the cost and timeline of CMC development by replacing exploratory experiments with targeted ones.

---

## 8. Likely Interview Questions and Answers

**Q: Walk me through how the model works.**
A: The model describes four coupled ODEs — one each for substrate concentration A, product B, impurity C, and dissolved hydrogen H2. At each time step, the solver computes how fast A is being consumed by the primary reaction, how fast B is being produced, how fast the secondary reaction converts B to C, and how fast H2 is being transferred from the gas phase and consumed. I used `scipy.integrate.solve_ivp` to integrate these over 120 minutes, with fed-batch substrate addition handled as a continuous input term in the A equation. The model outputs conversion, impurity fraction, and H2 limitation metrics at the end of the batch.

**Q: Why did you choose Radau as the solver?**
A: The system is stiff. Stiffness arises because the H2 mass transfer dynamics operate on a much faster timescale than the reaction kinetics — kLa is around 0.8/min but the reaction timescale is tens of minutes. Explicit solvers like RK45 handle stiffness by taking very small steps to stay stable, which makes them slow and sometimes unreliable for this kind of problem. Radau is an implicit solver designed for stiff ODEs; it can take larger steps by solving an internal nonlinear system at each step, making it both faster and more robust for this application.

**Q: What does kLa represent physically?**
A: kLa is the volumetric mass transfer coefficient for gas-liquid transfer, with units of 1/min (or 1/s). Physically, k is the individual mass transfer coefficient at the gas-liquid interface and a is the specific interfacial area — the surface area of gas bubbles per unit volume of liquid. The product kLa captures how quickly the dissolved gas concentration moves toward its equilibrium (saturation) value. In a real reactor, kLa is increased by faster agitation, finer bubble size, and higher gas flow rate. It decreases at manufacturing scale primarily because the power-to-volume ratio drops and bubble coalescence increases.

**Q: What is the difference between your selectivity and your conversion?**
A: Conversion answers the question "how much of the starting material A has been consumed?" — it is (A0 - A) / A0. Selectivity answers a different question: "of the A that did react, how much ended up as the desired product B versus the impurity C?" In my model I track impurity as a fraction of total product formed, which is a related but distinct metric. You can have high conversion with poor selectivity — the high catalyst scenario demonstrates this: 97.7% conversion but 26.6% impurity, meaning a significant fraction of the converted material ended up as C rather than B.

**Q: How would you validate this model?**
A: The primary validation approach would be lab-scale experiments with deliberate variation of kLa, feed rate, and catalyst loading. I would measure dissolved H2 profiles over time using an in-line H2 sensor or dissolved oxygen as a proxy, and take timed aliquots for GC or HPLC analysis to get A, B, and C concentrations over the course of the batch. Fitting k1, k2, and kLa to that data would test whether the model structure is correct, not just whether it can reproduce a single endpoint. A secondary validation would be comparing model predictions against a scenario not used in fitting — a genuine predictive test.

**Q: What would you change if you had more time?**
A: Four things. First, add Arrhenius temperature dependence so the model can handle non-isothermal operation and test cooling system requirements. Second, replace the empirical kinetics with a Langmuir-Hinshelwood mechanism to better capture behaviour at high concentrations. Third, run a Monte Carlo sensitivity analysis to propagate parameter uncertainty into the output distributions rather than just doing one-at-a-time sweeps. Fourth, fit the model to actual experimental data to move it from a screening tool to a quantitatively predictive one.

**Q: What does the design space plot tell you?**
A: The design space plot shows, for a grid of kLa and feed rate combinations, whether the process meets both the conversion target and the impurity limit. Green zones are operating points that pass both criteria, yellow zones fail one, and red zones fail both. The plot makes it immediately clear that acceptable operation requires kLa above roughly 0.4/min — below that, even optimal feed rate cannot recover conversion. This is directly analogous to the ICH Q8 design space concept: the plot defines where you can operate and still guarantee product quality, and the boundary of the green zone is where you would set your control strategy.

**Q: Why is the impurity higher in the high-catalyst scenario?**
A: The secondary reaction rate is k2 * B * H2. When k1 is high, substrate A is consumed rapidly in the early part of the batch, so product B accumulates quickly and at high concentration while dissolved H2 is still available. The ratio B/A is high early on, which means the k2 * B * H2 term is large relative to the primary reaction — the impurity pathway runs faster than it does at base conditions. Essentially, the catalyst does not distinguish between the primary and secondary reactions; it accelerates both, but the secondary reaction benefits more because it is favoured by the higher B concentration that the fast primary reaction creates.

**Q: What is the practical significance of the 100% H2-limitation result in the low kLa scenario?**
A: At kLa = 0.2/min, the rate at which the reaction consumes dissolved H2 exceeds the rate at which mass transfer can replenish it, so dissolved H2 drops to near zero almost immediately and stays there for the entire batch. This is not just a quantitative reduction in rate — it is a qualitative change in operating regime. The reactor is no longer kinetically limited; it is supply-limited, and no adjustment to catalyst loading, temperature, or feed rate will help without first fixing the H2 supply. This is exactly what a scale-up engineer needs to know before committing to a pilot campaign.

**Q: How does this relate to what Polymodels Hub does?**
A: Polymodels Hub focuses on process modelling to de-risk pharmaceutical development and support CMC strategy. This project is a direct example of that: rather than running an expensive design-of-experiments campaign at lab scale and discovering kLa sensitivity empirically, a model identifies it upfront and tells you where to look. That reduces experimental cost, shortens timelines, and gives the regulatory team quantitative evidence to support process controls in a submission — which is exactly the value proposition of process modelling in drug development.
