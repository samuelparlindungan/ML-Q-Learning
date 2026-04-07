import numpy as np
import matplotlib.pyplot as plt
import os


def main():
    # 1. Setup Folder
    output_dir = "output"
    if not os.path.exists(output_dir):
        print(f"Error: Folder '{output_dir}' tidak ditemukan.")
        return

    print("Sedang memuat data training...")

    # 2. Load Data .npy (Sesuai output dari main_training.py)
    try:
        reward_log = np.load(f"{output_dir}/reward_log.npy")
        step_log = np.load(f"{output_dir}/step_log.npy")
        qmax_log = np.load(f"{output_dir}/qmax_log.npy")
        alpha_log = np.load(f"{output_dir}/alpha_log.npy")
        state_visit = np.load(f"{output_dir}/state_visit.npy")
        action_count = np.load(f"{output_dir}/action_count.npy")
    except FileNotFoundError as e:
        print(f"Error: File data tidak lengkap. Pastikan training sudah selesai.\n{e}")
        return

    # Konfigurasi visual
    window = 50  # Untuk menghaluskan garis (Moving Average)
    plt.style.use("default")  # Menggunakan style standar

    # --- GRAFIK 1: Konvergensi Reward (Bukti Agen Belajar) ---
    print("1. Membuat Grafik Reward...")
    plt.figure(figsize=(10, 6))

    # Hitung rata-rata bergerak agar grafik lebih mulus dibaca
    moving_avg = np.convolve(reward_log, np.ones(window) / window, mode="valid")

    plt.plot(reward_log, alpha=0.3, color="blue", label="Raw Reward")
    plt.plot(
        range(window - 1, len(reward_log)),
        moving_avg,
        color="red",
        linewidth=2,
        label="Rata-rata (Moving Avg)",
    )

    plt.title("Konvergensi Reward per Episode")
    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(
        f"{output_dir}/Grafik_1_Konvergensi_Reward.png", dpi=300
    )  # Simpan High Quality
    plt.close()

    # --- GRAFIK 2: Efisiensi Langkah (Bukti Agen Makin Cepat) ---
    print("2. Membuat Grafik Steps...")
    plt.figure(figsize=(10, 6))

    steps_ma = np.convolve(step_log, np.ones(window) / window, mode="valid")

    plt.plot(step_log, alpha=0.3, color="green", label="Steps")
    plt.plot(
        range(window - 1, len(step_log)),
        steps_ma,
        color="darkgreen",
        linewidth=2,
        label="Rata-rata Steps",
    )

    plt.title("Efisiensi Langkah Menuju Target")
    plt.xlabel("Episode")
    plt.ylabel("Jumlah Langkah (Steps)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{output_dir}/Grafik_2_Efisiensi_Steps.png", dpi=300)
    plt.close()

    # --- GRAFIK 3: Penurunan Learning Rate (Alpha Decay) ---
    print("3. Membuat Grafik Alpha...")
    plt.figure(figsize=(10, 6))
    plt.plot(alpha_log, color="orange", linewidth=2)
    plt.title("Penurunan Learning Rate (Alpha Decay)")
    plt.xlabel("Episode")
    plt.ylabel("Nilai Alpha")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{output_dir}/Grafik_3_Alpha_Decay.png", dpi=300)
    plt.close()

    # --- GRAFIK 4: Heatmap Kunjungan State (Dimana Agen Sering Berada?) ---
    print("4. Membuat Heatmap Kunjungan State...")
    plt.figure(figsize=(8, 6))

    # Reshape array 25 state menjadi matrix 5x5 (pH x EC)
    state_matrix = state_visit.reshape(5, 5)

    plt.imshow(state_matrix, cmap="YlOrRd", aspect="auto")
    cbar = plt.colorbar()
    cbar.set_label("Frekuensi Kunjungan")

    # Label Sumbu
    plt.xlabel("Indeks EC (0:VL - 4:VH)")
    plt.ylabel("Indeks pH (0:VL - 4:VH)")
    plt.title("Heatmap Kunjungan Agen pada State Space")

    # Tambahkan angka di setiap kotak
    for i in range(5):
        for j in range(5):
            plt.text(
                j, i, int(state_matrix[i, j]), ha="center", va="center", color="black"
            )

    plt.savefig(f"{output_dir}/Grafik_4_Heatmap_State.png", dpi=300)
    plt.close()

    # --- GRAFIK 5: Distribusi Aksi (Apa yang sering dilakukan Agen?) ---
    print("5. Membuat Histogram Aksi...")
    plt.figure(figsize=(10, 6))

    action_names = [
        "Idle",
        "pH Up(S)",
        "pH Up(L)",
        "pH Dn(S)",
        "pH Dn(L)",
        "Nut(S)",
        "Nut(L)",
        "Air(S)",
        "Air(L)",
    ]

    plt.bar(action_names, action_count, color="purple")
    plt.title("Distribusi Aksi yang Diambil Agen")
    plt.xlabel("Jenis Aksi")
    plt.ylabel("Frekuensi")
    plt.xticks(rotation=45)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/Grafik_5_Distribusi_Aksi.png", dpi=300)
    plt.close()

    print(f"\n✅ Selesai! Cek 5 file gambar (.png) di folder '{output_dir}/'")


if __name__ == "__main__":
    main()
