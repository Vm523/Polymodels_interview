"""Default simulation parameters for fed-batch hydrogenation model."""

# Kinetic parameters
K1 = 1.5           # A + H2 -> B  [L/(mol·min)]
K2 = 0.008         # B + H2 -> C  [L/(mol·min)]

# Mass transfer
KLA = 0.8          # kLa for H2  [1/min]
H2_SAT_BASE = 0.05 # H2 saturation at 1 bar  [mol/L]
H2_PRESSURE = 3.0  # operating hydrogen pressure [bar]

# Feed conditions
FEED_RATE = 0.05   # volumetric feed rate  [L/min]
FEED_CONC_A = 2.0  # substrate concentration in feed  [mol/L]

# Initial conditions
V0 = 1.0           # initial volume  [L]
A0 = 0.0           # initial substrate conc  [mol/L]
B0 = 0.0           # initial product conc  [mol/L]
C0 = 0.0           # initial impurity conc  [mol/L]
H2_0 = 0.0         # initial dissolved H2  [mol/L]

# Batch parameters
T_END = 120.0      # batch time  [min]
N_EVAL = 500       # number of time points for output

# Risk thresholds
CONVERSION_TARGET = 0.95    # minimum acceptable conversion
IMPURITY_THRESHOLD = 0.05   # maximum acceptable C/(B+C)  [mol fraction]
H2_LIMITATION_THRESHOLD = 0.06  # H2 below 40% of H2_sat = mass transfer limited  [mol/L]
