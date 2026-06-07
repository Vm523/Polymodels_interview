"""
ODE model for fed-batch catalytic hydrogenation.

Reactions:
    A + H2 -> B  (desired)
    B + H2 -> C  (side reaction / over-hydrogenation)

State vector: [A, B, C, H2, V]
"""

import numpy as np


def h2_saturation(pressure, h2_sat_base=0.05):
    """Return dissolved H2 saturation using simplified Henry's law.

    H2_sat scales linearly with pressure relative to 1 bar baseline.
    """
    return h2_sat_base * pressure


def reaction_rates(A, B, H2, k1, k2):
    """Return (r1, r2) reaction rates in mol/(L·min).

    Both reactions are second-order: first order in the organic substrate
    and first order in dissolved H2. Instantaneous selectivity = r1/(r1+r2)
    = k1*A / (k1*A + k2*B). As A depletes and B accumulates late in the
    batch, B/A rises and the side reaction becomes increasingly dominant —
    the main driver of over-hydrogenation impurity.
    """
    r1 = k1 * A * H2  # A + H2 -> B
    r2 = k2 * B * H2  # B + H2 -> C  (over-hydrogenation)
    return r1, r2


def odes(t, y, params):
    """ODE right-hand side for fed-batch hydrogenation.

    Called repeatedly by solve_ivp. t is required by the solver API
    but unused here because the system is autonomous (no explicit time
    dependence — isothermal, constant pressure assumed).

    Parameters
    ----------
    t : float
        Current time [min] — required by solve_ivp, not used in equations
    y : array-like
        State [A, B, C, H2, V]
    params : dict
        Model parameters

    Returns
    -------
    list
        Derivatives [dA/dt, dB/dt, dC/dt, dH2/dt, dV/dt]
    """
    A, B, C, H2, V = y
    # Guard against small negatives that stiff solvers can produce
    A = max(A, 0.0)
    B = max(B, 0.0)
    C = max(C, 0.0)
    H2 = max(H2, 0.0)
    V = max(V, 1e-9)

    k1 = params['k1']
    k2 = params['k2']
    kla = params['kla']
    h2_sat = params['h2_sat']
    feed_rate = params['feed_rate']
    feed_conc_a = params['feed_conc_a']

    r1, r2 = reaction_rates(A, B, H2, k1, k2)
    mt = kla * (h2_sat - H2)  # H2 mass transfer: driving force is deficit from saturation
    dilution = feed_rate / V  # D = F/V: how fast the growing volume dilutes everything

    # Each balance: [molar input from feed] - [dilution loss] - [reaction loss/gain]
    dA  =  feed_rate * feed_conc_a / V  - dilution * A  - r1           # substrate: fed in, diluted, consumed
    dB  =                               - dilution * B  + r1  - r2     # product:   diluted, formed, over-hydrogenated
    dC  =                               - dilution * C         + r2    # impurity:  diluted, formed by side reaction
    dH2 =  mt                           - dilution * H2 - r1  - r2     # H2:        transferred in, diluted, consumed by both reactions
    dV  =  feed_rate                                                    # volume grows at feed rate

    return [dA, dB, dC, dH2, dV]
