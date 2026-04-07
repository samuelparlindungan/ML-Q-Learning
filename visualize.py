import numpy as np  # Import numpy for numerical operations and arrays
import matplotlib.pyplot as plt  # Import matplotlib for plotting
import os  # Import os for file path operations

# Pastikan kita di direktori yang benar
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script directory
output_dir = os.path.join(script_dir, "output")  # Set output directory path

reward = np.load(os.path.join(output_dir, "reward_log.npy"))  # Load reward log
steps = np.load(os.path.join(output_dir, "step_log.npy"))  # Load step log
qmax = np.load(os.path.join(output_dir, "qmax_log.npy"))  # Load qmax log
alpha = np.load(os.path.join(output_dir, "alpha_log.npy"))  # Load alpha log
state_visit = np.load(
    os.path.join(output_dir, "state_visit.npy")
)  # Load state visit counts
action_count = np.load(
    os.path.join(output_dir, "action_count.npy")
)  # Load action counts

# 1. Reward Convergence
window = 50  # Set moving average window size
moving_avg = np.convolve(
    reward, np.ones(window) / window, mode="valid"
)  # Calculate moving average
plt.figure(figsize=(10, 6))  # Create figure
plt.plot(reward, alpha=0.3, label="Reward", color="blue")  # Plot raw rewards
plt.plot(  # Plot moving average
    range(window - 1, len(reward)),
    moving_avg,
    linewidth=2,
    label="Moving Avg (50)",
    color="red",
)
plt.xlabel("Episode")  # Set x label
plt.ylabel("Total Reward")  # Set y label
plt.title("Konvergensi Reward")  # Set title
plt.legend()  # Show legend
plt.grid(alpha=0.3)  # Add grid
plt.tight_layout()  # Adjust layout
plt.show()  # Display plot

# 2. Q-max Convergence dengan Moving Average
plt.figure(figsize=(10, 6))  # Create figure
qmax_ma = np.convolve(
    qmax, np.ones(window) / window, mode="valid"
)  # Calculate moving average for qmax
plt.plot(qmax, alpha=0.3, label="Q-max", color="green")  # Plot raw qmax
plt.plot(  # Plot moving average
    range(window - 1, len(qmax)),
    qmax_ma,
    linewidth=2,
    label="Moving Avg (50)",
    color="darkgreen",
)
plt.xlabel("Episode")  # Set x label
plt.ylabel("Max Q Value")  # Set y label
plt.title("Konvergensi Nilai Q (dengan Adaptive Learning Rate)")  # Set title
plt.legend()  # Show legend
plt.grid(alpha=0.3)  # Add grid
plt.tight_layout()  # Adjust layout
plt.show()  # Display plot

# 3. Alpha Decay
plt.figure(figsize=(10, 6))  # Create figure
plt.plot(alpha, linewidth=2, color="orange")  # Plot alpha decay
plt.xlabel("Episode")  # Set x label
plt.ylabel("Learning Rate (Alpha)")  # Set y label
plt.title("Decay Learning Rate")  # Set title
plt.grid(alpha=0.3)  # Add grid
plt.tight_layout()  # Adjust layout
plt.show()  # Display plot

# 4. Step Efficiency
plt.figure(figsize=(10, 6))  # Create figure
steps_ma = np.convolve(
    steps, np.ones(window) / window, mode="valid"
)  # Calculate moving average for steps
plt.plot(steps, alpha=0.3, label="Steps", color="purple")  # Plot raw steps
plt.plot(  # Plot moving average
    range(window - 1, len(steps)),
    steps_ma,
    linewidth=2,
    label="Moving Avg (50)",
    color="darkviolet",
)
plt.xlabel("Episode")  # Set x label
plt.ylabel("Jumlah Langkah")  # Set y label
plt.title("Efisiensi Menuju State Optimal")  # Set title
plt.legend()  # Show legend
plt.grid(alpha=0.3)  # Add grid
plt.tight_layout()  # Adjust layout
plt.show()  # Display plot

# 5. State Visitation Heatmap
plt.figure(figsize=(8, 6))  # Create figure
state_matrix = state_visit.reshape(5, 5)  # Reshape state visits to 5x5 matrix
im = plt.imshow(state_matrix, cmap="YlOrRd", aspect="auto")  # Create heatmap
plt.colorbar(im, label="Frekuensi Kunjungan")  # Add colorbar
plt.xlabel("EC Index")  # Set x label
plt.ylabel("pH Index")  # Set y label
plt.title("Heatmap Kunjungan State")  # Set title
for i in range(5):  # Loop over rows
    for j in range(5):  # Loop over columns
        text = plt.text(  # Add text annotation
            j,
            i,
            int(state_matrix[i, j]),
            ha="center",
            va="center",
            color="black",
            fontsize=10,
        )
plt.tight_layout()  # Adjust layout
plt.show()  # Display plot

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
