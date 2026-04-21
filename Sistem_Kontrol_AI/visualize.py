import numpy as np  # Import numpy for numerical operations and arrays
import matplotlib.pyplot as plt  # Import matplotlib for plotting
import os  # Import os for file path operations

# ==========================================
# 0. KONFIGURASI VERSI (Otomatis dari env)
# ==========================================
from env_ph_ec import PhEcEnv

env = PhEcEnv()
# Kita coba cari folder dataset_asli dulu, kalau tidak ada pakai yang biasa
VERSION = f"{env.ACTIVE_VERSION}_dataset_asli"
OUT_DIR = f"../output/{VERSION}"

if not os.path.exists(OUT_DIR):
    # Fallback untuk folder lama tanpa suffix _asli
    VERSION_OLD = f"{env.ACTIVE_VERSION}_dataset"
    OUT_DIR_OLD = f"../output/{VERSION_OLD}"
    if os.path.exists(OUT_DIR_OLD):
        VERSION = VERSION_OLD
        OUT_DIR = OUT_DIR_OLD

if not os.path.exists(OUT_DIR):
    print(f"Error: Folder '{OUT_DIR}' tidak ditemukan.")
    exit()

reward = np.load(f"{OUT_DIR}/reward_log.npy")  # Load reward log
steps = np.load(f"{OUT_DIR}/step_log.npy")  # Load step log
qmax = np.load(f"{OUT_DIR}/qmax_log.npy")  # Load qmax log
alpha = np.load(f"{OUT_DIR}/alpha_log.npy")  # Load alpha log
state_visit = np.load(f"{OUT_DIR}/state_visit.npy")  # Load state visit counts
action_count = np.load(f"{OUT_DIR}/action_count.npy")  # Load action counts

# 1. Reward Convergence
window = 50
moving_avg = np.convolve(reward, np.ones(window) / window, mode="valid")
plt.figure(figsize=(10, 6))
plt.plot(reward, alpha=0.3, label="Reward", color="blue")
plt.plot(
    range(window - 1, len(reward)),
    moving_avg,
    linewidth=2,
    label="Moving Avg (50)",
    color="red",
)
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.title("Konvergensi Reward")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/1_reward_convergence.png")  # SAVE
plt.show()

# 2. Q-max Convergence
plt.figure(figsize=(10, 6))
qmax_ma = np.convolve(qmax, np.ones(window) / window, mode="valid")
plt.plot(qmax, alpha=0.3, label="Q-max", color="green")
plt.plot(
    range(window - 1, len(qmax)),
    qmax_ma,
    linewidth=2,
    label="Moving Avg (50)",
    color="darkgreen",
)
plt.xlabel("Episode")
plt.ylabel("Max Q Value")
plt.title("Konvergensi Nilai Q")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/2_qmax_convergence.png")  # SAVE
plt.show()

# 3. Alpha Decay
plt.figure(figsize=(10, 6))
plt.plot(alpha, linewidth=2, color="orange")
plt.xlabel("Episode")
plt.ylabel("Learning Rate (Alpha)")
plt.title("Decay Learning Rate")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/3_alpha_decay.png")  # SAVE
plt.show()

# 4. Step Efficiency
plt.figure(figsize=(10, 6))
steps_ma = np.convolve(steps, np.ones(window) / window, mode="valid")
plt.plot(steps, alpha=0.3, label="Steps", color="purple")
plt.plot(
    range(window - 1, len(steps)),
    steps_ma,
    linewidth=2,
    label="Moving Avg (50)",
    color="darkviolet",
)
plt.xlabel("Episode")
plt.ylabel("Jumlah Langkah")
plt.title("Efisiensi Menuju State Optimal")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/4_step_efficiency.png")  # SAVE
plt.show()

# 5. State Visitation Heatmap
plt.figure(figsize=(8, 6))
state_matrix = state_visit.reshape(5, 5)
im = plt.imshow(state_matrix, cmap="YlOrRd", aspect="auto")
plt.colorbar(im, label="Frekuensi Kunjungan")
plt.xlabel("EC Index")
plt.ylabel("pH Index")
plt.title("Heatmap Kunjungan State")
for i in range(5):
    for j in range(5):
        plt.text(j, i, int(state_matrix[i, j]), ha="center", va="center", color="black")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/5_state_heatmap.png")  # SAVE
plt.show()

# 6. Action Distribution
plt.figure(figsize=(10, 6))  # Create figure
action_names = [  # List of action names
    "IDLE",
    "pH Up S",
    "pH Up L",
    "pH Down S",
    "pH Down L",
    "Nutrisi S",
    "Nutrisi L",
    "Air Baku S",
    "Air Baku L",
]
plt.bar(range(9), action_count, color="steelblue")  # Create bar plot
plt.xlabel("Action")  # Set x label
plt.ylabel("Frekuensi")  # Set y label
plt.title("Distribusi Aksi Agen")  # Set title
plt.xticks(range(9), action_names, rotation=45, ha="right")  # Set x ticks
plt.grid(alpha=0.3, axis="y")  # Add grid
plt.tight_layout()  # Adjust layout
plt.savefig(f"{OUT_DIR}/6_action_dist.png")  # SAVE PNG
plt.show()  # Display plot

print("\n📊 STATISTIK TRAINING:")  # Print statistics header
print(f"Total Episodes: {len(reward)}")  # Print total episodes
print(
    f"Reward Akhir (avg 100 ep): {np.mean(reward[-100:]):.1f}"
)  # Print final average reward
print(
    f"Steps Akhir (avg 100 ep): {np.mean(steps[-100:]):.1f}"
)  # Print final average steps
print(
    f"Q-max Akhir (avg 100 ep): {np.mean(qmax[-100:]):.1f}"
)  # Print final average qmax
print(f"Alpha Akhir: {alpha[-1]:.4f}")  # Print final alpha
print(  # Print most visited state
    f"State paling sering dikunjungi: {np.argmax(state_visit)} (count: {int(np.max(state_visit))})"
)
print(  # Print most used action
    f"Action paling sering digunakan: {np.argmax(action_count)} (count: {int(np.max(action_count))})"
)
