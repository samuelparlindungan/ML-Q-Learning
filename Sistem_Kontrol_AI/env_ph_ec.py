import gymnasium as gym  # Import gymnasium library for creating reinforcement learning environments
from gymnasium import (
    spaces,
)  # Import spaces module for defining observation and action spaces
import numpy as np  # Import numpy for numerical operations and arrays
import random  # Import random for generating random numbers


class PhEcEnv(
    gym.Env
):  # Define the PhEcEnv class inheriting from gym.Env for custom environment
    def __init__(self):  # Initialize the environment instance
        super().__init__()  # Call parent class initializer
        # 25 states: 5 pH levels x 5 EC levels (sesuai Tabel 3.3)
        self.observation_space = spaces.Discrete(
            25
        )  # Define observation space as 25 discrete states
        # 9 actions: sesuai Tabel 3.4 (Idle, pH Up Short/Long, dll.)
        self.action_space = spaces.Discrete(
            9
        )  # Define action space as 9 discrete actions
        # Target state: pH index 2, EC index 2 (State 13, indeks 12 di 0-based)
        self.optimal_ph = 2  # Set optimal pH index
        self.optimal_ec = 2  # Set optimal EC index
        # Critical states untuk inisialisasi training (zona Kritis/Kritis Ekstrem)
        self.critical_states = [
            0,
            1,
            2,
            3,
            4,
            5,
            9,
            10,
            14,
            15,
            19,
            20,
            21,
            22,
            23,
            24,
        ]  # List of critical states for initialization
        # Reward table sesuai Tabel 3.6 (zona-based)
        self.reward_table = self._build_reward()  # Build and assign reward table

    def _build_reward(self):  # Private method to build the reward table
        r = np.full(25, 0.0)  # Initialize reward array with 25 zeros
        # Kritis Ekstrem: -120 (States 1,5,21,25 -> indeks 0,4,20,24)
        extreme = [0, 4, 20, 24]  # List of extreme critical state indices
        for s in extreme:  # Loop through extreme states
            r[s] = -120.0  # Assign reward for extreme states
        # Kritis: -80 (States 2,3,4,6,10,11,15,16,20,22,23,24 -> indeks 1,2,3,5,9,10,14,15,19,21,22,23)
        kritis = [
            1,
            2,
            3,
            5,
            9,
            10,
            14,
            15,
            19,
            21,
            22,
            23,
        ]  # List of critical state indices
        for s in kritis:  # Loop through critical states
            r[s] = -80.0  # Assign reward for critical states
        # Transisi: -5 (States 7,9,17,19 -> indeks 6,8,16,18)
        transisi = [6, 8, 16, 18]  # List of transition state indices
        for s in transisi:  # Loop through transition states
            r[s] = -5.0  # Assign reward for transition states
        # Sub-Optimal: +10 (States 8,12,14,18 -> indeks 7,11,13,17)
        sub_optimal = [7, 11, 13, 17]  # List of sub-optimal state indices
        for s in sub_optimal:  # Loop through sub-optimal states
            r[s] = 10.0  # Assign reward for sub-optimal states
        # Target: +50 (State 13 -> indeks 12)
        r[12] = 50.0  # Assign reward for target state
        return r  # Return the reward array

    def reset(self, seed=None, options=None):  # Reset the environment to initial state
        # Inisialisasi acak dari critical states untuk training
        crit_idx = np.random.choice(
            self.critical_states
        )  # Randomly choose a critical state index
        self.ph = crit_idx // 5 + random.uniform(
            -0.4, 0.4
        )  # Set initial pH with random variation
        self.ec = crit_idx % 5 + random.uniform(
            -0.4, 0.4
        )  # Set initial EC with random variation
        state = int(
            np.clip(round(self.ph), 0, 4)
        ) * 5 + int(  # Calculate discrete state from pH and EC
            np.clip(round(self.ec), 0, 4)  # Clip EC to valid range
        )
        return state, {}  # Return initial state and empty info dict

    # ======================================================================
    # --- KONFIGURASI VERSI (PILIH v1, v2, atau v3) ---
    # ======================================================================
    ACTIVE_VERSION = "v3"  # <--- GANTI DI SINI (Ubah ke "v2" atau "v1" jika perlu)
    # ======================================================================

    def step(self, action):  # Execute one step in the environment
        delta_ph, delta_ec = 0.0, 0.0  # Initialize changes in pH and EC

        if self.ACTIVE_VERSION == "v1":
            # [v1: TEORI] - Desain Awal
            if action == 1:
                delta_ph, delta_ec = 0.50, 0.0
            elif action == 2:
                delta_ph, delta_ec = 1.00, 0.0
            elif action == 3:
                delta_ph, delta_ec = -0.50, 0.0
            elif action == 4:
                delta_ph, delta_ec = -1.00, 0.0
            elif action == 5:
                delta_ph, delta_ec = 0.00, 0.50
            elif action == 6:
                delta_ph, delta_ec = 0.00, 1.00
            elif action == 7:
                delta_ph, delta_ec = 0.00, -0.50
            elif action == 8:
                delta_ph, delta_ec = 0.00, -1.00

        elif self.ACTIVE_VERSION == "v2":
            # [v2: DATASET SESI 1 (16-04-2026)] - Kalibrasi Tahap 1
            if action == 1:
                delta_ph, delta_ec = 0.15, 25.6
            elif action == 2:
                delta_ph, delta_ec = 0.28, 28.1
            elif action == 3:
                delta_ph, delta_ec = -0.10, 32.9
            elif action == 4:
                delta_ph, delta_ec = -0.41, 10.0
            elif action == 5:
                delta_ph, delta_ec = -0.03, 78.8
            elif action == 6:
                delta_ph, delta_ec = -0.15, 132.0
            elif action == 7:
                delta_ph, delta_ec = -0.02, 17.2
            elif action == 8:
                delta_ph, delta_ec = -0.00, 13.4

        elif self.ACTIVE_VERSION == "v3":
            # [v3: DATASET SESI 2 (21-04-2026)] - Kalibrasi Tahap 2 (FINAL)
            if action == 1:
                delta_ph, delta_ec = 0.20, 0.0
            elif action == 2:
                delta_ph, delta_ec = 0.45, 10.0
            elif action == 3:
                delta_ph, delta_ec = -0.25, 30.0
            elif action == 4:
                delta_ph, delta_ec = -0.16, 40.0
            elif action == 5:
                delta_ph, delta_ec = -0.02, 75.0
            elif action == 6:
                delta_ph, delta_ec = -0.18, 276.0
            elif action == 7:
                delta_ph, delta_ec = -0.02, -290.0
            elif action == 8:
                delta_ph, delta_ec = -0.00, -400.0
        # ======================================================================

        """
        # --- LOGIKA LAMA (SIMULASI TEORI) - DIKOMENTARI ---
        if action == 1:  # If action is pH Up Short
            delta_ph = 0.5  # pH Up Short
        elif action == 2:  # If action is pH Up Long
            delta_ph = 1.0  # pH Up Long
        elif action == 3:  # If action is pH Down Short
            delta_ph = -0.5  # pH Down Short
        elif action == 4:  # If action is pH Down Long
            delta_ph = -1.0  # pH Down Long
        elif action == 5:  # If action is Nutrisi Short
            delta_ec = 0.5  # Nutrisi Short
        elif action == 6:  # If action is Nutrisi Long
            delta_ec = 1.0  # Nutrisi Long
        elif action == 7:  # If action is Air Baku Short
            delta_ec = -0.5  # Air Baku Short
        elif action == 8:  # If action is Air Baku Long
            delta_ec = -1.0  # Air Baku Long
        """
        # Natural drift (Disesuaikan agar lebih realistis dengan tandon asli)
        drift_ph = random.uniform(-0.02, 0.02)  # Perubahan pH alami kecil
        drift_ec = random.uniform(
            -5.0, 5.0
        )  # Perubahan EC alami (noise arus/homogenisasi)
        self.ph += delta_ph + drift_ph
        self.ec += delta_ec + drift_ec

        # Sensor noise (Akurasi pembacaan sensor)
        measured_ph = self.ph + random.uniform(-0.01, 0.01)
        measured_ec = self.ec + random.uniform(-2.0, 2.0)

        # Discretization
        ph_d = int(np.clip(round(measured_ph), 0, 4))  # Discretize pH to 0-4
        ec_d = int(np.clip(round(measured_ec), 0, 4))  # Discretize EC to 0-4
        state = ph_d * 5 + ec_d  # Calculate new state index
        reward = self.reward_table[state]  # Get reward for current state
        terminated = (
            ph_d == self.optimal_ph and ec_d == self.optimal_ec
        )  # Check if terminated (reached optimal)
        truncated = False  # Set truncated to False (not used)
        return state, reward, terminated, truncated, {}  # Return step results
