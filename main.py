from main_algo import BinaryPSO
from parameter import (
    DESIGN_PATH, QOR_MODE,
    N_PARTICLES, N_DIMENSIONS, MAX_ITER,
    INERTIA, COGNITIVE, SOCIAL
)

import time
import os
import csv


def save_results_to_csv(bitstring, score, elapsed_time):
    os.makedirs("logs", exist_ok=True)
    csv_path = "logs/final_result.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Best Score (QoR)", score])
        writer.writerow(["Improvement (%)", (1 - score / 2) * 100])
        writer.writerow(["Elapsed Time (s)", elapsed_time])
        writer.writerow([])
        writer.writerow(["Bit Index", "Bit Value"])
        for idx, val in enumerate(bitstring):
            writer.writerow([idx, val])
    print(f"[📄] Results saved to {csv_path}")


def print_summary(bitstring, score, elapsed_time):
    print("\n[RESULTS]")
    print(f"Best Position (binary): {''.join(map(str, bitstring))}")
    print(f"Best Score (QoR): {score:.6f}")
    print(f"QoR Improvement: {(1 - score / 2) * 100:.2f}%")
    print(f"Elapsed Time: {elapsed_time:.2f} seconds")
    print("-" * 34)


if __name__ == "__main__":
    print(f"[STARTING] Binary PSO Optimization for {DESIGN_PATH}")
    print(f"   Mode: {QOR_MODE.upper()} | Particles: {N_PARTICLES} | Iterations: {MAX_ITER}")

    start_time = time.time()

    b_pso = BinaryPSO(N_PARTICLES, N_DIMENSIONS, MAX_ITER, INERTIA, COGNITIVE, SOCIAL)
    best_position, best_score = b_pso.optimize(DESIGN_PATH, qor_mode=QOR_MODE)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print_summary(best_position, best_score, elapsed_time)
    save_results_to_csv(best_position, best_score, elapsed_time)
