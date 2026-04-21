import pandas as pd
import matplotlib.pyplot as plt
import os

# Konfigurasi Folder & File
INPUT_FILE = "../dataset_acak_qlearning.csv"
BASE_OUTPUT_DIR = "../output_data"


def generate_plots():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: File {INPUT_FILE} tidak ditemukan!")
        return

    # Load Data
    df_all = pd.read_csv(INPUT_FILE)

    # Pilih Sesi
    sessions = df_all["Sesi_Eksperimen"].unique()
    print("\nSesi yang tersedia:")
    for i, s in enumerate(sessions):
        print(f"{i+1}. {s}")

    try:
        pilihan = int(
            input(
                "\nPilih nomor sesi yang ingin divisualisasikan (atau 0 untuk semua): "
            )
        )
        if pilihan == 0:
            target_session = None
            df = df_all
            session_name = "Semua_Sesi"
        else:
            target_session = sessions[pilihan - 1]
            df = df_all[df_all["Sesi_Eksperimen"] == target_session].reset_index(
                drop=True
            )
            session_name = target_session
    except:
        print("Pilihan tidak valid, memproses semua data...")
        df = df_all
        session_name = "Semua_Sesi"

    # Buat Folder Output Spesifik Sesi
    output_dir = os.path.join(BASE_OUTPUT_DIR, session_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Memproses {len(df)} baris data untuk sesi: {session_name}...")

    # 1. Grafik Pergerakan pH dan EC dengan Anotasi Aksi
    plt.figure(figsize=(15, 10))

    # Subplot pH
    plt.subplot(2, 1, 1)
    plt.plot(df.index, df["pH_St"], marker="o", color="b", alpha=0.3, label="Alur pH")
    # Tambahkan Anotasi Nomor Aksi
    for i, txt in enumerate(df["Action"]):
        plt.annotate(
            f"A{txt}",
            (i, df["pH_St"][i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color="darkblue",
        )
    plt.ylabel("Nilai pH")
    plt.title(f"Tren pH & EC - Sesi: {session_name}")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    # Subplot EC
    plt.subplot(2, 1, 2)
    plt.plot(df.index, df["EC_St"], marker="s", color="g", alpha=0.3, label="Alur EC")
    # Tambahkan Anotasi Nomor Aksi
    for i, txt in enumerate(df["Action"]):
        plt.annotate(
            f"A{txt}",
            (i, df["EC_St"][i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color="darkgreen",
        )
    plt.ylabel("Nilai EC")
    plt.xlabel("Urutan Langkah (Step)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "1_tren_diagnostic_ph_ec.png"))
    print(f"Saved: {output_dir}/1_tren_diagnostic_ph_ec.png")

    # 2. Grafik Distribusi Aksi (Bar Chart)
    plt.figure(figsize=(10, 5))
    action_counts = df["Action"].value_counts().sort_index()
    action_counts.plot(kind="bar", color="orange", edgecolor="black")
    plt.title(f"Distribusi Frekuensi Aksi - Sesi: {session_name}")
    plt.xlabel("ID Aksi")
    plt.ylabel("Jumlah Kemunculan")
    plt.xticks(rotation=0)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.savefig(os.path.join(output_dir, "2_distribusi_aksi.png"))
    print(f"Saved: {output_dir}/2_distribusi_aksi.png")

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

    plt.suptitle(f"Analisis Delta - Sesi: {session_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "3_efek_aksi_boxplot.png"))
    print(f"Saved: {output_dir}/3_efek_aksi_boxplot.png")

    # 4. Grafik Perbandingan Antar Sesi (Overlaid)
    plt.figure(figsize=(15, 10))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    # Subplot pH Comparison
    plt.subplot(2, 1, 1)
    for i, s_name in enumerate(sessions):
        s_df = df_all[df_all["Sesi_Eksperimen"] == s_name].reset_index(drop=True)
        plt.plot(
            s_df.index,
            s_df["pH_St"],
            label=f"pH - {s_name}",
            color=colors[i % len(colors)],
            alpha=0.8,
            linewidth=2,
        )
    plt.ylabel("Nilai pH")
    plt.title("Perbandingan Tren Antar Sesi: pH")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    # Subplot EC Comparison
    plt.subplot(2, 1, 2)
    for i, s_name in enumerate(sessions):
        s_df = df_all[df_all["Sesi_Eksperimen"] == s_name].reset_index(drop=True)
        plt.plot(
            s_df.index,
            s_df["EC_St"],
            label=f"EC - {s_name}",
            color=colors[i % len(colors)],
            alpha=0.8,
            linewidth=2,
        )
    plt.ylabel("Nilai EC")
    plt.xlabel("Langkah ke- (Step)")
    plt.title("Perbandingan Tren Antar Sesi: EC")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()

    plt.tight_layout()
    comparison_dir = os.path.join(BASE_OUTPUT_DIR, "Perbandingan_Sesi")
    os.makedirs(comparison_dir, exist_ok=True)
    plt.savefig(os.path.join(comparison_dir, "4_komparasi_sesi_overlaid.png"))
    print(f"Saved: {comparison_dir}/4_komparasi_sesi_overlaid.png")

    print("\n" + "=" * 60)
    print(f"DATA BERHASIL DIEKSTRAK KE FOLDER: {output_dir}")
    print(f"GRAFIK KOMPARASI ADA DI: {comparison_dir}")
    print("=" * 60)


if __name__ == "__main__":
    generate_plots()
