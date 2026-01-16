# parameter.py

# PSO settings
ABC_LIB_PATH = "/home/zenyth/Desktop/abcdef/asap7.lib"
N_PARTICLES = 100
N_DIMENSIONS = 80
MAX_ITER = 100
INERTIA = 5
COGNITIVE = 1.7
SOCIAL = 1.3

# Optimization target
QOR_MODE = "combined"  # options: "lut", "level", "combined"
DESIGN_PATH = "benchmarks/arithmetic/log2.blif"

# QoR tuning
STALL_LIMIT = 15
EXPLORE_TRIGGER = 10
MUTATION_RATE = 0.2

# Plot and log
CONVERGENCE_PLOT_PATH = "logs/convergence_plot.png"
