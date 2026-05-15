"""
generate_grafik_bab4.py
=======================
Script untuk menghasilkan grafik-grafik Bab 4 skripsi Samuel P.
Kualitas tinggi (300 DPI) untuk disisipkan ke dokumen Word.

CARA PAKAI:
1. Jalankan script ini dari folder Sistem_Kontrol_AI
2. Grafik akan tersimpan di folder 'output/output_grafik/'

DEPENDENCIES:
   pip install numpy pandas matplotlib
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import os

# ============================================================
# KONFIGURASI PATH
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
OUT_DIR = os.path.join(BASE_DIR, "output", "output_grafik")

# File Data
REWARD_FILE = os.path.join(BASE_DIR, "output", "v6_final", "reward_log.npy")
STEP_FILE = os.path.join(BASE_DIR, "output", "v6_final", "step_log.npy")
CSV_FILE = os.path.join(BASE_DIR, "output", "data_transisi_otomatis.csv")

DPI = 300  # Resolusi Cetak
ROLLING_WIN = 150  # Window rolling average

os.makedirs(OUT_DIR, exist_ok=True)

# Font konsisten Times New Roman (sesuai format skripsi)
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.dpi": DPI,
    }
)


# ============================================================
# HELPER
# ============================================================
def save(fig, filename):
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  [OK] {path}")


def get_ph_idx(ph):
    if ph < 5.5:
        return 0
    elif ph < 5.8:
        return 1
    elif ph <= 6.2:
        return 2
    elif ph <= 6.5:
        return 3
    else:
        return 4


def get_ec_idx(ec):
    if ec < 800:
        return 0
    elif ec < 1100:
        return 1
    elif ec <= 1300:
        return 2
    elif ec <= 1600:
        return 3
    else:
        return 4


# ============================================================
# GAMBAR 4.1 — Kurva Reward per Episode
# ============================================================
if os.path.exists(REWARD_FILE):
    print("\n[1/4] Membuat Gambar 4.1 — Kurva Reward...")
    reward_log = np.load(REWARD_FILE)
    episodes = np.arange(1, len(reward_log) + 1)
    rolling_r = pd.Series(reward_log).rolling(ROLLING_WIN, min_periods=1).mean().values

    conv_ep = next(
        (i for i in range(ROLLING_WIN, len(rolling_r)) if rolling_r[i] > 0), None
    )

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(
        episodes,
        reward_log,
        color="#B0C4DE",
        alpha=0.30,
        linewidth=0.4,
        label="Reward per Episode",
        zorder=1,
    )
    ax.plot(
        episodes,
        rolling_r,
        color="#1A5276",
        linewidth=2.0,
        label=f"Rata-rata Bergerak ({ROLLING_WIN} Episode)",
        zorder=3,
    )
    ax.axhline(
        0,
        color="#E74C3C",
        linestyle="--",
        linewidth=1.0,
        alpha=0.75,
        label="Reward = 0",
        zorder=2,
    )

    if conv_ep:
        ax.axvline(
            conv_ep,
            color="#27AE60",
            linestyle=":",
            linewidth=1.3,
            alpha=0.85,
            label=f"Konvergensi Positif (Ep. {conv_ep:,})",
            zorder=2,
        )

    ax.set_xlabel("Episode Pelatihan")
    ax.set_ylabel("Total Reward Kumulatif")
    ax.set_title(
        "Gambar Kurva Total Reward per Episode Selama 10.000 Episode Pelatihan",
        fontweight="bold",
        pad=10,
    )
    ax.set_xlim(1, len(reward_log))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(loc="upper left", framealpha=0.85)
    ax.grid(True, alpha=0.25, linewidth=0.5)
    fig.tight_layout()
    save(fig, "gambar_4_1_reward.png")
else:
    print(f"[SKIP] File {REWARD_FILE} tidak ditemukan.")

# ============================================================
# GAMBAR 4.2 — Kurva Langkah per Episode
# ============================================================
if os.path.exists(STEP_FILE):
    print("[2/4] Membuat Gambar 4.2 — Kurva Steps...")
    step_log = np.load(STEP_FILE)
    episodes = np.arange(1, len(step_log) + 1)
    rolling_s = pd.Series(step_log).rolling(ROLLING_WIN, min_periods=1).mean().values

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(
        episodes,
        step_log,
        color="#F0B27A",
        alpha=0.30,
        linewidth=0.4,
        label="Langkah per Episode",
        zorder=1,
    )
    ax.plot(
        episodes,
        rolling_s,
        color="#784212",
        linewidth=2.0,
        label=f"Rata-rata Bergerak ({ROLLING_WIN} Episode)",
        zorder=3,
    )
    ax.axhline(
        200,
        color="#7F8C8D",
        linestyle="--",
        linewidth=0.8,
        alpha=0.6,
        label="Batas Maks. Langkah (200)",
        zorder=2,
    )

    ax.set_xlabel("Episode Pelatihan")
    ax.set_ylabel("Jumlah Langkah per Episode")
    ax.set_title(
        "Gambar Kurva Jumlah Langkah per Episode Selama 10.000 Episode Pelatihan",
        fontweight="bold",
        pad=10,
    )
    ax.set_xlim(1, len(step_log))
    ax.set_ylim(0, 215)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(loc="upper left", framealpha=0.85)
    ax.grid(True, alpha=0.25, linewidth=0.5)
    fig.tight_layout()
    save(fig, "gambar_4_2_steps.png")
else:
    print(f"[SKIP] File {STEP_FILE} tidak ditemukan.")

# ============================================================
# GAMBAR 4.3 — Time-series pH dan EC (Respon Kendali)
# ============================================================
if os.path.exists(CSV_FILE):
    print("[3/4] Membuat Gambar 4.3 — Respon Kendali...")
    df = pd.read_csv(CSV_FILE)
    steps = np.arange(1, len(df) + 1)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"hspace": 0.08}
    )

    ax1.plot(
        steps,
        df["pH_St"],
        "o-",
        color="#2980B9",
        linewidth=1.4,
        markersize=3.5,
        label="pH (Sₜ)",
        zorder=3,
    )
    ax1.plot(
        steps,
        df["pH_St+1"],
        "s--",
        color="#154360",
        linewidth=1.4,
        markersize=3.5,
        alpha=0.75,
        label="pH (Sₜ₊₁)",
        zorder=3,
    )
    ax1.axhspan(
        5.8,
        6.2,
        alpha=0.10,
        color="#27AE60",
        label="Zona Optimal pH (5,8 – 6,2)",
        zorder=1,
    )
    ax1.set_ylabel("Nilai pH")
    ax1.set_ylim(5.5, 6.75)
    ax1.legend(loc="upper right", framealpha=0.85)
    ax1.grid(True, alpha=0.25, linewidth=0.5)
    ax1.set_title(
        "Gambar Respon Kendali pH dan EC Sistem Otomatis", fontweight="bold", pad=10
    )

    ax2.plot(
        steps,
        df["EC_St"],
        "o-",
        color="#E74C3C",
        linewidth=1.4,
        markersize=3.5,
        label="EC (Sₜ)",
        zorder=3,
    )
    ax2.plot(
        steps,
        df["EC_St+1"],
        "s--",
        color="#7B241C",
        linewidth=1.4,
        markersize=3.5,
        alpha=0.75,
        label="EC (Sₜ₊₁)",
        zorder=3,
    )
    ax2.axhspan(
        1100,
        1300,
        alpha=0.10,
        color="#27AE60",
        label="Zona Optimal EC (1.100 – 1.300 µS/cm)",
        zorder=1,
    )
    ax2.set_xlabel("Langkah Kendali (Step)")
    ax2.set_ylabel("Nilai EC (µS/cm)")
    ax2.legend(loc="upper left", framealpha=0.85)
    ax2.grid(True, alpha=0.25, linewidth=0.5)

    # fig.tight_layout() # Sering error dengan sharex dan manual hspace
    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.95, hspace=0.15)
    save(fig, "gambar_4_3_respon.png")
else:
    print(f"[SKIP] File {CSV_FILE} tidak ditemukan.")

# ============================================================
# GAMBAR 4.4 — Distribusi Kunjungan State
# ============================================================
if os.path.exists(CSV_FILE):
    print("[4/4] Membuat Gambar Distribusi State...")
    df["state_t"] = df.apply(
        lambda r: get_ph_idx(r["pH_St"]) * 5 + get_ec_idx(r["EC_St"]) + 1, axis=1
    )
    state_counts = df["state_t"].value_counts().sort_index()

    zone_color = {
        "ekstrem": "#E74C3C",
        "kritis": "#F39C12",
        "transisi": "#F4D03F",
        "suboptimal": "#52BE80",
        "target": "#1A5276",
    }
    ZONE_MAP = {
        1: "ekstrem",
        5: "ekstrem",
        21: "ekstrem",
        25: "ekstrem",
        2: "kritis",
        3: "kritis",
        4: "kritis",
        6: "kritis",
        10: "kritis",
        11: "kritis",
        15: "kritis",
        16: "kritis",
        20: "kritis",
        22: "kritis",
        23: "kritis",
        24: "kritis",
        7: "transisi",
        9: "transisi",
        17: "transisi",
        19: "transisi",
        8: "suboptimal",
        12: "suboptimal",
        14: "suboptimal",
        18: "suboptimal",
        13: "target",
    }

    colors = [zone_color[ZONE_MAP.get(s, "kritis")] for s in state_counts.index]
    labels = [f"S{s}" for s in state_counts.index]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.bar(
        labels,
        state_counts.values,
        color=colors,
        edgecolor="white",
        linewidth=0.6,
        zorder=2,
    )

    for bar, val in zip(bars, state_counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.25,
            str(val),
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_xlabel("State ID")
    ax.set_ylabel("Frekuensi Kunjungan")
    ax.set_title(
        "Gambar 4.4 Distribusi Kunjungan State Selama Sesi Kendali Otomatis",
        fontweight="bold",
        pad=10,
    )
    ax.grid(True, alpha=0.25, linewidth=0.5, axis="y", zorder=1)
    ax.set_ylim(0, state_counts.max() + 4)
    fig.tight_layout()
    save(fig, "gambar_4_4_state_dist.png")

print(f"\nSemua grafik tersimpan di folder '{OUT_DIR}/'")
