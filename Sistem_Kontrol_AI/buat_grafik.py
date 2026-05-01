import numpy as np
import matplotlib.pyplot as plt
import os


def main():
    # 1. Definisi Semua Versi Penelitian
    ALL_VERSIONS = [
        "v1_teori",
        "v2_dataset_asli",
        "v3_dataset_asli",
        "v4_dataset_asli",
        "v5_normal_sesi3",
        "v6_lama",
        "v6_final",  # Hasil Akhir (Bab 4)
    ]

    # Ambil lokasi folder project secara absolut
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

    print("=" * 60)
    print("[AI] BATCH REPORT GENERATOR: GRAFIK RISET AI")
    print("=" * 60)

    for version in ALL_VERSIONS:
        # Arahkan ke folder output di dalam project root
        output_dir = os.path.normpath(os.path.join(PROJECT_ROOT, "output", version))

        if not os.path.exists(output_dir):
            print(f"[SKIP] {version}: Folder tidak ditemukan di {output_dir}")
            continue

        print(f"\n[PROCESS] MEMPROSES VERSI: {version.upper()}")
        print("-" * 30)

        # 2. Load Data .npy
        try:
            reward_log = np.load(f"{output_dir}/reward_log.npy")
            step_log = np.load(f"{output_dir}/step_log.npy")
            qmax_log = np.load(f"{output_dir}/qmax_log.npy")
            alpha_log = np.load(f"{output_dir}/alpha_log.npy")
            state_visit = np.load(f"{output_dir}/state_visit.npy")
            action_count = np.load(f"{output_dir}/action_count.npy")
        except Exception as e:
            print(f"[ERROR] saat memuat data {version}: {e}")
            continue

        # Konfigurasi visual
        window = 50
        plt.style.use("default")

        # --- GRAFIK 1: Reward ---
        print("   -> Membuat Grafik Reward...")
        plt.figure(figsize=(10, 6))
        moving_avg = np.convolve(reward_log, np.ones(window) / window, mode="valid")
        plt.plot(reward_log, alpha=0.3, color="blue", label="Raw Reward")
        plt.plot(
            range(window - 1, len(reward_log)),
            moving_avg,
            color="red",
            linewidth=2,
            label="Rata-rata",
        )
        plt.title(f"Konvergensi Reward ({version})")
        plt.xlabel("Episode")
        plt.ylabel("Total Reward")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/Grafik_1_Konvergensi_Reward.png", dpi=200)
        plt.close()

        # --- GRAFIK 2: Steps ---
        print("   -> Membuat Grafik Steps...")
        plt.figure(figsize=(10, 6))
        steps_ma = np.convolve(step_log, np.ones(window) / window, mode="valid")
        plt.plot(step_log, alpha=0.3, color="green", label="Steps")
        plt.plot(
            range(window - 1, len(step_log)), steps_ma, color="darkgreen", linewidth=2
        )
        plt.title(f"Efisiensi Langkah ({version})")
        plt.xlabel("Episode")
        plt.ylabel("Jumlah Langkah")
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/Grafik_2_Efisiensi_Steps.png", dpi=200)
        plt.close()

        # --- GRAFIK 3: Alpha ---
        print("   -> Membuat Grafik Alpha...")
        plt.figure(figsize=(10, 6))
        plt.plot(alpha_log, color="orange", linewidth=2)
        plt.title(f"Alpha Decay ({version})")
        plt.xlabel("Episode")
        plt.ylabel("Nilai Alpha")
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/Grafik_3_Alpha_Decay.png", dpi=200)
        plt.close()

        # --- GRAFIK 4: Heatmap ---
        print("   -> Membuat Heatmap State...")
        plt.figure(figsize=(8, 6))
        state_matrix = state_visit.reshape(5, 5)
        plt.imshow(state_matrix, cmap="YlOrRd", aspect="auto")
        plt.colorbar(label="Frekuensi Kunjungan")
        plt.title(f"Heatmap State Space ({version})")
        for i in range(5):
            for j in range(5):
                plt.text(
                    j,
                    i,
                    int(state_matrix[i, j]),
                    ha="center",
                    va="center",
                    color="black",
                )
        plt.savefig(f"{output_dir}/Grafik_4_Heatmap_State.png", dpi=200)
        plt.close()

        # --- GRAFIK 5: Aksi ---
        print("   -> Membuat Histogram Aksi...")
        plt.figure(figsize=(10, 6))
        action_names = [
            "Idle",
            "pHUp(S)",
            "pHUp(L)",
            "pHDn(S)",
            "pHDn(L)",
            "Nut(S)",
            "Nut(L)",
            "Air(S)",
            "Air(L)",
        ]
        plt.bar(action_names, action_count, color="purple")
        plt.title(f"Distribusi Aksi ({version})")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/Grafik_5_Distribusi_Aksi.png", dpi=200)
        plt.close()

        print(f"[DONE] Versi {version} SELESAI.")

    print("\n" + "=" * 60)
    print("SELESAI! Semua grafik riset telah diperbarui.")
    print("=" * 60)


if __name__ == "__main__":
    main()
