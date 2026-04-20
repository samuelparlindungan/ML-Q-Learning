import pandas as pd
import matplotlib.pyplot as plt
import os

# Konfigurasi Folder & File
INPUT_FILE = "../dataset_acak_qlearning_tanpa_waktu.csv"
OUTPUT_DIR = "../output_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_plots():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: File {INPUT_FILE} tidak ditemukan!")
        return

    # Load Data
    df = pd.read_csv(INPUT_FILE)
    print(f"Memproses {len(df)} baris data...")

    # 1. Grafik Pergerakan pH dan EC dengan Anotasi Aksi
    plt.figure(figsize=(15, 10))

    # Subplot pH
    plt.subplot(2, 1, 1)
    plt.plot(
        df["Cycle"], df["pH_St"], marker="o", color="b", alpha=0.3, label="Alur pH"
    )
    # Tambahkan Anotasi Nomor Aksi
    for i, txt in enumerate(df["Action"]):
        plt.annotate(
            f"A{txt}",
            (df["Cycle"][i], df["pH_St"][i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color="darkblue",
        )
    plt.ylabel("Nilai pH")
    plt.title("Detail Diagnostik: Tren pH & EC dengan Anotasi Aksi (A1-A8)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    # Subplot EC
    plt.subplot(2, 1, 2)
    plt.plot(
        df["Cycle"], df["EC_St"], marker="s", color="g", alpha=0.3, label="Alur EC"
    )
    # Tambahkan Anotasi Nomor Aksi
    for i, txt in enumerate(df["Action"]):
        plt.annotate(
            f"A{txt}",
            (df["Cycle"][i], df["EC_St"][i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color="darkgreen",
        )
    plt.ylabel("Nilai EC")
    plt.xlabel("Siklus ke-")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "1_tren_diagnostic_ph_ec.png"))
    print(f"Saved: 1_tren_diagnostic_ph_ec.png (dengan Anotasi)")

    # 2. Grafik Distribusi Aksi (Bar Chart)
    plt.figure(figsize=(10, 5))
    action_counts = df["Action"].value_counts().sort_index()
    action_counts.plot(kind="bar", color="orange", edgecolor="black")
    plt.title("Distribusi Frekuensi Aksi (1-8)")
    plt.xlabel("ID Aksi")
    plt.ylabel("Jumlah Kemunculan")
    plt.xticks(rotation=0)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.savefig(os.path.join(OUTPUT_DIR, "2_distribusi_aksi.png"))
    print(f"Saved: 2_distribusi_aksi.png")

    # 3. Grafik Efek Aksi (Delta pH vs Delta EC per Aksi)
    plt.figure(figsize=(12, 6))

    # Delta pH per Aksi
    plt.subplot(1, 2, 1)
    df.boxplot(column="Delta_pH", by="Action", ax=plt.gca())
    plt.title("Efek Aksi terhadap pH (Delta)")
    plt.ylabel("Perubahan pH")

    # Delta EC per Aksi
    plt.subplot(1, 2, 2)
    df.boxplot(column="Delta_EC", by="Action", ax=plt.gca())
    plt.title("Efek Aksi terhadap EC (Delta)")
    plt.ylabel("Perubahan EC")

    plt.suptitle("")  # Menghilangkn default title pandas
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "3_efek_aksi_boxplot.png"))
    print(f"Saved: 3_efek_aksi_boxplot.png")

    print("\n" + "=" * 40)
    print(f"SEMUA GRAFIK BERHASIL DIEKSTRAK KE FOLDER: {OUTPUT_DIR}")
    print("=" * 40)


if __name__ == "__main__":
    generate_plots()
