"""
generate_grafik_lampiran.py
===========================
Script untuk menghasilkan grafik tren pH dan EC per sesi eksplorasi
untuk Lampiran skripsi Samuel P.
Kualitas tinggi (300 DPI) untuk disisipkan ke dokumen Word.

CARA PAKAI:
1. Letakkan file ini satu folder dengan:
   - dataset_acak_qlearning.csv
2. Jalankan: python generate_grafik_lampiran.py
3. Grafik akan tersimpan di folder 'output_lampiran/'

DEPENDENCIES:
   pip install numpy pandas matplotlib
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ============================================================
# KONFIGURASI
# ============================================================
CSV_FILE  = "dataset_acak_qlearning.csv"
OUT_DIR   = "output/output_lampiran"
DPI       = 300

os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family":      "serif",
    "font.serif":       ["Times New Roman", "DejaVu Serif"],
    "axes.titlesize":   11,
    "axes.labelsize":   10,
    "xtick.labelsize":  8,
    "ytick.labelsize":  8,
    "legend.fontsize":  7,
    "figure.dpi":       DPI,
})

# ============================================================
# KONFIGURASI AKSI
# ============================================================
action_names = {
    1: "pH Up Short",   2: "pH Up Long",
    3: "pH Down Short", 4: "pH Down Long",
    5: "Nutrisi Short", 6: "Nutrisi Long",
    7: "Air Baku Short",8: "Air Baku Long"
}

action_colors = {
    1: "#2980B9", 2: "#1A5276",
    3: "#E74C3C", 4: "#922B21",
    5: "#27AE60", 6: "#1E8449",
    7: "#F39C12", 8: "#D68910"
}

# Batas anomali berdasarkan batas fisik pompa
BATAS_ANOMALI_PH = 1.5    # |ΔpH| > nilai ini = anomali
BATAS_ANOMALI_EC = 400    # |ΔEC| > nilai ini = anomali

# ============================================================
# LOAD DATA
# ============================================================
if not os.path.exists(CSV_FILE):
    # Coba cek di folder atas jika dijalankan dari subfolder
    if os.path.exists("../" + CSV_FILE):
        CSV_FILE = "../" + CSV_FILE
    else:
        print(f"[ERROR] File {CSV_FILE} tidak ditemukan!")
        exit()

df = pd.read_csv(CSV_FILE)
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed')

sesi_list = df['Sesi_Eksperimen'].unique()
print(f"Dataset dimuat: {len(df)} baris, {len(sesi_list)} sesi\n")

# ============================================================
# GENERATE GRAFIK PER SESI
# ============================================================
for sesi in sesi_list:
    sub = df[df['Sesi_Eksperimen'] == sesi].reset_index(drop=True)
    n_sesi = sesi.split('_')[-1]  # "1", "2", "3", "4"
    cycles = sub['Cycle']

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 6),
        sharex=True,
        gridspec_kw={"hspace": 0.06}
    )

    # ----------------------------------------------------------
    # PANEL ATAS: pH
    # ----------------------------------------------------------
    ax1.plot(cycles, sub['pH_St'], 'o-',
             color='#5D6D7E', linewidth=1.2, markersize=3,
             label='pH Awal (St)', zorder=2)
    ax1.plot(cycles, sub['pH_St1'], 's--',
             color='#1A5276', linewidth=1.2, markersize=3, alpha=0.8,
             label='pH Akhir (St+1)', zorder=2)
    ax1.axhspan(5.8, 6.2, alpha=0.10, color='#27AE60',
                label='Zona Optimal (5,8–6,2)', zorder=1)

    # Tandai anomali pH
    anom_ph = sub[sub['Delta_pH'].abs() > BATAS_ANOMALI_PH]
    if not anom_ph.empty:
        ax1.scatter(anom_ph['Cycle'], anom_ph['pH_St1'],
                    color='red', s=100, zorder=5,
                    marker='X', label='Anomali (dieliminasi)')
        for _, r in anom_ph.iterrows():
            ax1.annotate(
                f"ΔpH={r['Delta_pH']:.2f}",
                xy=(r['Cycle'], r['pH_St1']),
                xytext=(r['Cycle'] + 1, r['pH_St1'] + 0.18),
                arrowprops=dict(arrowstyle='->', color='red', lw=0.8),
                fontsize=7.5, color='red'
            )

    ax1.set_ylabel('Nilai pH')
    ax1.legend(loc='upper right', framealpha=0.85, ncol=2)
    ax1.grid(True, alpha=0.25, linewidth=0.5)
    ax1.set_title(
        f'Tren pH dan EC Sesi Eksplorasi {n_sesi} (n={len(sub)} observasi)',
        fontweight='bold', pad=8
    )

    # ----------------------------------------------------------
    # PANEL BAWAH: EC
    # ----------------------------------------------------------
    ax2.plot(cycles, sub['EC_St'], 'o-',
             color='#5D6D7E', linewidth=1.2, markersize=3,
             label='EC Awal (St)', zorder=2)
    ax2.plot(cycles, sub['EC_St1'], 's--',
             color='#922B21', linewidth=1.2, markersize=3, alpha=0.8,
             label='EC Akhir (St+1)', zorder=2)
    ax2.axhspan(1100, 1300, alpha=0.10, color='#27AE60',
                label='Zona Optimal (1.100–1.300 µS/cm)', zorder=1)

    # Tandai anomali EC
    anom_ec = sub[sub['Delta_EC'].abs() > BATAS_ANOMALI_EC]
    if not anom_ec.empty:
        ax2.scatter(anom_ec['Cycle'], anom_ec['EC_St1'],
                    color='red', s=100, zorder=5,
                    marker='X', label='Anomali (dieliminasi)')
        for _, r in anom_ec.iterrows():
            ax2.annotate(
                f"ΔEC={r['Delta_EC']:.0f}",
                xy=(r['Cycle'], r['EC_St1']),
                xytext=(r['Cycle'] + 0.5, r['EC_St1'] + 60),
                arrowprops=dict(arrowstyle='->', color='red', lw=0.8),
                fontsize=7.5, color='red'
            )

    # Warnai background per aksi
    for _, row in sub.iterrows():
        ax2.axvspan(
            row['Cycle'] - 0.4, row['Cycle'] + 0.4,
            alpha=0.06,
            color=action_colors.get(row['Action'], 'gray'),
            zorder=0
        )

    ax2.set_ylabel('Nilai EC (µS/cm)')
    ax2.set_xlabel('Cycle (Langkah Eksperimen)')
    ax2.legend(loc='upper right', framealpha=0.85, ncol=2)
    ax2.grid(True, alpha=0.25, linewidth=0.5)

    # Legend aksi di pojok kanan bawah
    unique_acts = sorted(sub['Action'].unique())
    legend_acts = [
        mpatches.Patch(
            facecolor=action_colors[a], alpha=0.5,
            label=action_names[a]
        )
        for a in unique_acts if a in action_names
    ]
    if legend_acts:
        ax2.legend(
            handles=legend_acts,
            loc='lower right', fontsize=6.5,
            framealpha=0.85, ncol=4,
            title='Aksi yang Dieksekusi', title_fontsize=7
        )

    # ----------------------------------------------------------
    # SIMPAN
    # ----------------------------------------------------------
    path = os.path.join(OUT_DIR, f"lampiran_sesi_{n_sesi}.png")
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    # Hitung anomali sesi ini
    n_anom = len(sub[(sub['Delta_pH'].abs() > BATAS_ANOMALI_PH) |
                     (sub['Delta_EC'].abs() > BATAS_ANOMALI_EC)])
    print(f"[OK] Sesi {n_sesi}: {len(sub)} obs, {n_anom} anomali -> {path}")

# ============================================================
# SELESAI
# ============================================================
print(f"\nSemua grafik tersimpan di folder '{OUT_DIR}/'")
print("File yang dihasilkan:")
for f in sorted(os.listdir(OUT_DIR)):
    if f.endswith('.png'):
        size = os.path.getsize(os.path.join(OUT_DIR, f)) // 1024
        print(f"  {f}  ({size} KB)")
