import gymnasium as gym  # Import gymnasium library for creating reinforcement learning environments
from gymnasium import (
    spaces,
)  # Import spaces module for defining observation and action spaces
import numpy as np  # Import numpy for numerical operations and arrays

# random sudah diganti np.random.normal() di v5


class PhEcEnv(
    gym.Env
):  # Define the PhEcEnv class inheriting from gym.Env for custom environment
    def __init__(self):  # Initialize the environment instance
        super().__init__()  # Call parent class initializer
        # self.ACTIVE_VERSION = "v5_normal_sesi3"
        self.ACTIVE_VERSION = (
            "v6_final"  # v6: Gabungan Sesi 1-4 (Cleaned) + Anti-Hacking Logic
        )
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

        # Kritis Ekstrem: -40 (States 1,5,21,25 -> indeks 0,4,20,24)
        extreme = [0, 4, 20, 24]  # List of extreme critical state indices
        for s in extreme:  # Loop through extreme states
            # r[s] = -120.0  # Assign reward for extreme states
            r[s] = -40.0  # Assign reward for extreme states (Reward Shaping)

        # Kritis: -20 (States 2,3,4,6,10,11,15,16,20,22,23,24 -> indeks 1,2,3,5,9,10,14,15,19,21,22,23)
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
            # r[s] = -80.0  # Assign reward for critical states
            r[s] = -20.0  # Assign reward for critical states (Reward Shaping)

        # Transisi: -2 (States 7,9,17,19 -> indeks 6,8,16,18)
        transisi = [6, 8, 16, 18]  # List of transition state indices
        for s in transisi:  # Loop through transition states
            # r[s] = -5.0  # Assign reward for transition states
            r[s] = -2.0  # Assign reward for transition states (Reward Shaping)

        # Sub-Optimal: -1 (States 8,12,14,18 -> indeks 7,11,13,17)
        sub_optimal = [7, 11, 13, 17]  # List of sub-optimal state indices
        for s in sub_optimal:  # Loop through sub-optimal states
            # r[s] = 10.0  # Assign reward for sub-optimal states
            r[s] = -1.0  # Paksa agen untuk bergerak ke State 13 (Penalty per step)

        # Target: +100 (State 13 -> indeks 12)
        # r[12] = (
        #    50.0  # [AI BOOSTER] Hadiah Jackpot agar AI sangat termotivasi (aslinya 50)
        # )
        r[12] = (
            100.0  # [Reward Shaping] Insentif tinggi agar AI keluar dari local optima
        )
        return r  # Return the reward array

    def reset(self, seed=None, options=None):  # Reset the environment to initial state
        # Inisialisasi acak dari critical states untuk training
        crit_idx = np.random.choice(
            self.critical_states
        )  # Randomly choose a critical state index
        self.ph = crit_idx // 5 + np.random.uniform(
            -0.4, 0.4
        )  # Set initial pH with random variation
        self.ec = crit_idx % 5 + np.random.uniform(
            -0.4, 0.4
        )  # Set initial EC with random variation
        state = int(
            np.clip(round(self.ph), 0, 4)
        ) * 5 + int(  # Calculate discrete state from pH and EC
            np.clip(round(self.ec), 0, 4)  # Clip EC to valid range
        )
        return state, {}  # Return initial state and empty info dict

    def step(self, action):  # Execute one step in the environment
        delta_ph, delta_ec = 0.0, 0.0  # Initialize changes in pH and EC

        # ======================================================================
        # DATA EMPIRIS TRANSISI (Delta pH & Delta EC) - CLEANED
        # Diambil dari dataset_acak_qlearning.csv (Gabungan Sesi 1-4)
        # Filter: Membuang anomali sensor & lonjakan fisik yang mustahil
        # Tanggal: 2026-04-29
        # ======================================================================
        EC_SCALE = 0.01

        if action == 1:  # pH Up Short
            # delta_ph, delta_ec = 0.50, 0.0    # v1 (Teori)
            # delta_ph, delta_ec = 0.15, 25.6   # v2 (Sesi 1)
            # delta_ph, delta_ec = 0.20, 0.0    # v3 (Sesi 2)
            # delta_ph, delta_ec = 0.15, 40.0   # v4 (Sesi 3)
            # delta_ph = np.random.normal(0.095, 0.01)  # v5 (Sesi 3 Normal)
            # delta_ec = np.random.normal(40.88 * EC_SCALE, 16.11 * EC_SCALE) # v5
            delta_ph = np.random.normal(0.1311, 0.0813)  # v6 (Final: Sesi 1-4 Cleaned)
            delta_ec = np.random.normal(40.90 * EC_SCALE, 47.91 * EC_SCALE)

        elif action == 2:  # pH Up Long
            # delta_ph, delta_ec = 1.00, 0.0    # v1 (Teori)
            # delta_ph, delta_ec = 0.50, 48.2   # v2 (Sesi 1)
            # delta_ph, delta_ec = 0.45, 10.0   # v3 (Sesi 2)
            # delta_ph, delta_ec = 0.40, 27.5   # v4 (Sesi 3)
            # delta_ph = np.random.normal(0.404, 0.198)  # v5 (Sesi 3 Normal)
            # delta_ec = np.random.normal(27.53 * EC_SCALE, 17.29 * EC_SCALE) # v5
            delta_ph = np.random.normal(0.3315, 0.1679)  # v6 (Final: Sesi 1-4 Cleaned)
            delta_ec = np.random.normal(32.88 * EC_SCALE, 33.30 * EC_SCALE)

        elif action == 3:  # pH Down Short
            # delta_ph, delta_ec = -0.50, 0.0   # v1 (Teori)
            # delta_ph, delta_ec = -0.21, 2.0    # v2 (Sesi 1)
            # delta_ph, delta_ec = -0.25, 30.0  # v3 (Sesi 2)
            # delta_ph, delta_ec = -0.20, 2.0   # v4 (Sesi 3)
            # delta_ph = np.random.normal(-0.211, 0.112) # v5 (Sesi 3 Normal)
            # delta_ec = np.random.normal(2.39 * EC_SCALE, 20.22 * EC_SCALE) # v5
            delta_ph = np.random.normal(-0.1672, 0.1018)  # v6 (Final: Sesi 1-4 Cleaned)
            delta_ec = np.random.normal(26.50 * EC_SCALE, 54.25 * EC_SCALE)

        elif action == 4:  # pH Down Long
            # delta_ph, delta_ec = -1.00, 0.0   # v1 (Teori)
            # delta_ph, delta_ec = -0.42, 11.4   # v2 (Sesi 1)
            # delta_ph, delta_ec = -0.16, 40.0  # v3 (Sesi 2)
            # delta_ph, delta_ec = -0.60, 1.7   # v4 (Sesi 3)
            # delta_ph = np.random.normal(-0.594, 0.523) # v5 (Sesi 3 Normal)
            # delta_ec = np.random.normal(1.71 * EC_SCALE, 6.91 * EC_SCALE) # v5
            delta_ph = np.random.normal(-0.4015, 0.3578)  # v6 (Final: Sesi 1-4 Cleaned)
            delta_ec = np.random.normal(26.36 * EC_SCALE, 49.63 * EC_SCALE)

        elif action == 5:  # Nutrisi Short
            # delta_ph, delta_ec = 0.00, 0.50   # v1 (Teori)
            # delta_ph, delta_ec = -0.03, 78.8  # v2 (Sesi 1)
            # delta_ph, delta_ec = -0.02, 75.0  # v3 (Sesi 2)
            # delta_ph, delta_ec = -0.01, 30.0  # v4 (Sesi 3)
            # delta_ph = np.random.normal(-0.013, 0.054) # v5 (Sesi 3 Normal)
            # delta_ec = np.random.normal(29.68 * EC_SCALE, 30.33 * EC_SCALE) # v5
            delta_ph = np.random.normal(-0.0161, 0.0344)  # v6 (Final: Sesi 1-4 Cleaned)
            delta_ec = np.random.normal(57.68 * EC_SCALE, 53.26 * EC_SCALE)

        elif action == 6:  # Nutrisi Long
            # delta_ph, delta_ec = 0.00, 1.00   # v1 (Teori)
            # delta_ph, delta_ec = -0.15, 132.0 # v2 (Sesi 1)
            # delta_ph, delta_ec = -0.18, 276.0 # v3 (Sesi 2)
            # delta_ph, delta_ec = -0.05, 112.0 # v4 (Sesi 3)
            # delta_ph = np.random.normal(-0.050, 0.01)  # v5 (Sesi 3 Normal)
            # delta_ec = np.random.normal(112.74 * EC_SCALE, 35.45 * EC_SCALE) # v5
            delta_ph = np.random.normal(-0.1006, 0.1035)  # v6 (Final: Sesi 1-4 Cleaned)
            delta_ec = np.random.normal(163.92 * EC_SCALE, 78.06 * EC_SCALE)

        elif action == 7:  # Air Baku Short
            # delta_ph, delta_ec = 0.00, -0.50  # v1 (Teori)
            # delta_ph, delta_ec = -0.02, 17.2  # v2 (Sesi 1)
            # delta_ph, delta_ec = -0.02, -290.0 # v3 (Sesi 2)
            # delta_ph, delta_ec = 0.01, -3.1   # v4 (Sesi 3)
            # delta_ph = np.random.normal(0.013, 0.021)  # v5 (Sesi 3 Normal)
            # delta_ec = np.random.normal(-3.13 * EC_SCALE, 3.62 * EC_SCALE) # v5
            delta_ph = np.random.normal(-0.0039, 0.0246)  # v6 (Final: Sesi 1-4 Cleaned)
            delta_ec = np.random.normal(-30.32 * EC_SCALE, 94.89 * EC_SCALE)

        elif action == 8:  # Air Baku Long
            # delta_ph, delta_ec = 0.00, -1.00  # v1 (Teori)
            # delta_ph, delta_ec = -0.00, 13.4  # v2 (Sesi 1)
            # delta_ph, delta_ec = -0.00, -400.0 # v3 (Sesi 2)
            # delta_ph, delta_ec = 0.01, -1.8   # v4 (Sesi 3)
            # delta_ph = np.random.normal(0.015, 0.015)  # v5 (Sesi 3 Normal)
            # delta_ec = np.random.normal(-1.76 * EC_SCALE, 2.84 * EC_SCALE) # v5
            delta_ph = np.random.normal(0.0023, 0.0190)  # v6 (Final: Sesi 1-4 Cleaned)
            delta_ec = np.random.normal(3.58 * EC_SCALE, 31.70 * EC_SCALE)
        # ======================================================================

        # Natural drift (noise empiris dari tandon asli)
        drift_ph = np.random.normal(0.0, 0.01)  # Drift pH alami
        drift_ec = np.random.normal(
            0.0, 3.0 * EC_SCALE
        )  # Drift EC alami (homogenisasi)
        self.ph += delta_ph + drift_ph
        self.ec += delta_ec + drift_ec

        # Sensor noise (Akurasi pembacaan sensor)
        measured_ph = self.ph + np.random.normal(0.0, 0.005)
        measured_ec = self.ec + np.random.normal(0.0, 1.0 * EC_SCALE)

        # Discretization
        ph_d = int(np.clip(round(measured_ph), 0, 4))  # Discretize pH to 0-4
        ec_d = int(np.clip(round(measured_ec), 0, 4))  # Discretize EC to 0-4
        state = ph_d * 5 + ec_d  # Calculate new state index
        reward = self.reward_table[state]  # Get reward for current state

        # Sesuai instruksi Engineer: Jangan mati di State 13 (Non-Episodic Control)
        # Episode berakhir hanya jika masuk ke zona bahaya fisik (Extreme Critical)
        # extreme = [0, 4, 20, 24]
        terminated = state in [0, 4, 20, 24]

        truncated = False  # Set truncated to False (not used)
        return state, reward, terminated, truncated, {}  # Return step results


# ==========================================
# FUNGSI PEMBANTU GLOBAL (Untuk Deploy)
# ==========================================
def get_ph_idx(ph):
    """Konversi nilai pH ke index 0-4 sesuai Tabel 3.3 TA"""
    if ph < 5.5:
        return 0
    if ph < 5.8:
        return 1
    if ph <= 6.2:
        return 2  # Optimal
    if ph <= 6.5:
        return 3
    return 4


def get_ec_idx(ec):
    """Konversi nilai EC ke index 0-4 sesuai Tabel 3.3 TA"""
    if ec < 800:
        return 0
    if ec < 1100:
        return 1
    if ec <= 1300:
        return 2  # Optimal
    if ec <= 1600:
        return 3
    return 4


def get_reward(ph, ec):
    """Hitung reward menggunakan reward_table dari env yang sudah diinisialisasi"""
    env = PhEcEnv()
    state = get_ph_idx(ph) * 5 + get_ec_idx(ec)
    return env.reward_table[state]
