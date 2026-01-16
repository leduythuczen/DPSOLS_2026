import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.stats import qmc  # LHS for initialization

from BBox_synth import get_QoR
#from BBox_synth_R import get_QoR
from parameter import (
    STALL_LIMIT, EXPLORE_TRIGGER, MUTATION_RATE,
    CONVERGENCE_PLOT_PATH
)

class BinaryPSO:
    def __init__(self, n_particles, n_dimensions, max_iter, inertia, cognitive, social):
        self.n_particles = n_particles
        self.n_dimensions = n_dimensions
        self.max_iter = max_iter
        self.inertia_init = inertia
        self.cognitive = cognitive
        self.social = social

        self.positions = self.smart_initialize()
        self.velocities = np.random.uniform(-1, 1, size=(n_particles, n_dimensions))
        self.personal_best_positions = self.positions.copy()
        self.personal_best_scores = np.full(n_particles, float('inf'))
        self.global_best_position = None
        self.global_best_score = float('inf')

        self.elite_memory = []
        self.elite_capacity = 5
        self.convergence = []

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def smart_initialize(self):
        """Use Latin Hypercube Sampling to initialize binary positions."""
        sampler = qmc.LatinHypercube(d=self.n_dimensions)
        sample = sampler.random(n=self.n_particles)
        return (sample > 0.5).astype(int)

    def local_hill_climb(self, bitstring, design_path, qor_mode):
        best = bitstring.copy()
        best_score = get_QoR("".join(map(str, best)), design_path, qor_mode)
        for i in range(len(best)):
            mutated = best.copy()
            mutated[i] ^= 1
            score = get_QoR("".join(map(str, mutated)), design_path, qor_mode)
            if score != -1 and score < best_score:
                best, best_score = mutated, score
        return best, best_score

    def optimize(self, design_path, qor_mode="combined"):
        w_max, w_min = self.inertia_init, 0.4
        stall_counter = 0
        no_qor_improve_count = 0

        for iteration in range(self.max_iter):
            w = w_max - (w_max - w_min) * (iteration / self.max_iter)
            in_exploration = no_qor_improve_count >= EXPLORE_TRIGGER
            print(f"[INFO] Iteration {iteration+1}/{self.max_iter} — {'<< EXPLORATION >>' if in_exploration else '>> EXPLOITATION <<'}")

            for i in range(self.n_particles):
                bit_string = "".join(str(x) for x in self.positions[i])
                fitness = get_QoR(bit_string, design_path, qor_mode=qor_mode)
                if fitness == -1: fitness = 10.0
                if fitness < self.personal_best_scores[i]:
                    self.personal_best_scores[i] = fitness
                    self.personal_best_positions[i] = self.positions[i].copy()

            best_score = np.min(self.personal_best_scores)
            best_index = np.argmin(self.personal_best_scores)

            if best_score < self.global_best_score:
                self.global_best_score = best_score
                self.global_best_position = self.personal_best_positions[best_index].copy()
                stall_counter = 0
                no_qor_improve_count = 0
                self.elite_memory.append((self.global_best_position.copy(), best_score))
                self.elite_memory = sorted(self.elite_memory, key=lambda x: x[1])[:self.elite_capacity]
            else:
                stall_counter += 1
                no_qor_improve_count += 1

            self.convergence.append(self.global_best_score)

            for i in range(self.n_particles):
                if in_exploration:
                    explore_strength = 2.0 * (1 - iteration / self.max_iter)
                    self.velocities[i] = np.random.uniform(-explore_strength, explore_strength, size=self.n_dimensions)
                else:
                    r1 = np.random.rand(self.n_dimensions)
                    r2 = np.random.rand(self.n_dimensions)
                    cognitive = self.cognitive * r1 * (self.personal_best_positions[i] - self.positions[i])
                    social = self.social * r2 * (self.global_best_position - self.positions[i])
                    self.velocities[i] = w * self.velocities[i] + cognitive + social

                np.clip(self.velocities[i], -4, 4, out=self.velocities[i])
                sigmoid_velocity = self.sigmoid(self.velocities[i])
                self.positions[i] = np.where(np.random.rand(self.n_dimensions) < sigmoid_velocity, 1, 0)

            if stall_counter >= STALL_LIMIT:
                print("[STALL] Injecting diversity and elite memory...")
                mutation_mask = np.random.rand(self.n_particles, self.n_dimensions) < MUTATION_RATE
                self.positions = np.bitwise_xor(self.positions, mutation_mask.astype(int))
                for i in range(min(len(self.elite_memory), self.n_particles)):
                    self.positions[i] = self.elite_memory[i][0].copy()
                stall_counter = 0

            if iteration % 20 == 0 and iteration > 0:
                print("Refining best with hill climbing...")
                refined, refined_score = self.local_hill_climb(self.global_best_position.copy(), design_path, qor_mode)
                if refined_score < self.global_best_score:
                    self.global_best_position = refined
                    self.global_best_score = refined_score
                    print(":D Hill climbing improved QoR.")

            print(f"    Best Score This Iteration: {self.global_best_score:.6f} improve {((2-self.global_best_score)*50):.2f} %")

        os.makedirs(os.path.dirname(CONVERGENCE_PLOT_PATH), exist_ok=True)
        plt.plot(self.convergence, label="Best QoR")
        plt.xlabel("Iteration")
        plt.ylabel("QoR Score")
        plt.title("PSO Convergence")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(CONVERGENCE_PLOT_PATH)
        plt.show()

        return self.global_best_position, self.global_best_score

