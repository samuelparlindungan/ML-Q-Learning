"""
generate_grafik_bab4_v2.py
==========================
Script update untuk Bab 4 Samuel P.
Menghasilkan semua grafik dari file .npy training v6_final.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import seaborn as sns
import os

# ============================================================
# KONFIGURASI PATH
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
OUT_DIR    = os.path.join(BASE_DIR, "output", "output_grafik_training")

# Folder Sumber v6_final
V6_DIR = os.path.join(BASE_DIR, "output", "v6_final")

# File Data
REWARD_FILE  = os.path.join(V6_DIR, "reward_log.npy")
STEP_FILE    = os.path.join(V6_DIR, "step_log.npy")
Q_TABLE_FILE = os.path.join(V6_DIR, "Q_table.npy")
Q_MAX_FILE   = os.path.join(V6_DIR, "qmax_log.npy")
STATE_VISIT  = os.path.join(V6_DIR, "state_visit.npy")
ACTION_COUNT = os.path.join(V6_DIR, "action_count.npy")
CSV_FILE     = os.path.join(BASE_DIR, "output", "data_transisi_otomatis.csv")

DPI          = 300
ROLLING_WIN  = 200

os.makedirs(OUT_DIR, exist_ok=True)

# Font Skripsi
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.dpi": DPI,
})

ACTIONS = ["IDLE", "pH Up S", "pH Up L", "pH Down S", "pH Down L", "Nutrisi S", "Nutrisi L", "Air S", "Air L"]

# ============================================================
# 1. GAMBAR 4.5 — Q-Table Heatmap (Pasangan State-Action)
# ============================================================
if os.path.exists(Q_TABLE_FILE):
    print("\n[1/4] Membuat Gambar 4.5 — Q-Table Heatmap...")
    q_table = np.load(Q_TABLE_FILE) # Shape (25, 9)
    
    plt.figure(figsize=(12, 8))
    ax = sns.heatmap(q_table, annot=True, fmt=".1f", cmap="YlGnBu", 
                     xticklabels=ACTIONS, 
                     yticklabels=[f"S{i+1}" for i in range(25)],
                     cbar_kws={'label': 'Q-Value'})
    
    plt.title("Gambar 4.5 Heatmap Nilai Q untuk Pasangan State-Action (Model v6_final)", fontweight="bold", pad=15)
    plt.xlabel("Aksi (Actions)")
    plt.ylabel("ID State")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "gambar_4_5_qtable_heatmap.png"), dpi=DPI)
    plt.close()

# ============================================================
# 2. GAMBAR 4.6 — Progresi Q-Max (Kestabilan Belajar)
# ============================================================
if os.path.exists(Q_MAX_FILE):
    print("[2/4] Membuat Gambar 4.6 — Progresi Q-Max...")
    qmax_log = np.load(Q_MAX_FILE)
    episodes = np.arange(1, len(qmax_log) + 1)
    rolling_q = pd.Series(qmax_log).rolling(ROLLING_WIN).mean()

    plt.figure(figsize=(10, 5))
    plt.plot(episodes, qmax_log, color="#AED6F1", alpha=0.4, label="Q-Max per Episode")
    plt.plot(episodes, rolling_q, color="#1B4F72", linewidth=2, label=f"Rata-rata Bergerak ({ROLLING_WIN} Ep)")
    plt.title("Gambar 4.6 Progresi Nilai Maksimum Q (Q-Max) Selama Pelatihan", fontweight="bold")
    plt.xlabel("Episode")
    plt.ylabel("Nilai Q Maksimum")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "gambar_4_6_qmax_progression.png"), dpi=DPI)
    plt.close()

# ============================================================
# 3. GAMBAR 4.7 — Distribusi Kunjungan State (Training)
# ============================================================
if os.path.exists(STATE_VISIT):
    print("[3/4] Membuat Gambar 4.7 — Distribusi Kunjungan State...")
    state_visit = np.load(STATE_VISIT)
    states = [f"S{i+1}" for i in range(25)]

    plt.figure(figsize=(10, 5))
    colors = plt.cm.viridis(np.linspace(0, 1, 25))
    plt.bar(states, state_visit, color=colors, edgecolor="black", alpha=0.8)
    plt.title("Gambar 4.7 Distribusi Kunjungan State Selama 10.000 Episode Pelatihan", fontweight="bold")
    plt.xlabel("ID State")
    plt.ylabel("Total Kunjungan")
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "gambar_4_7_state_visit.png"), dpi=DPI)
    plt.close()

# ============================================================
# 4. GAMBAR 4.8 — Distribusi Pilihan Aksi (Training)
# ============================================================
if os.path.exists(ACTION_COUNT):
    print("[4/4] Membuat Gambar 4.8 — Distribusi Pilihan Aksi...")
    action_count = np.load(ACTION_COUNT)

    plt.figure(figsize=(10, 5))
    plt.bar(ACTIONS, action_count, color="#E67E22", edgecolor="black", alpha=0.8)
    plt.title("Gambar 4.8 Frekuensi Pemilihan Aksi oleh Agen Selama Pelatihan", fontweight="bold")
    plt.xlabel("Aksi")
    plt.ylabel("Total Kali Dipilih")
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "gambar_4_8_action_distribution.png"), dpi=DPI)
    plt.close()

print(f"\n[SELESAI] Grafik tambahan tersimpan di: {OUT_DIR}")
