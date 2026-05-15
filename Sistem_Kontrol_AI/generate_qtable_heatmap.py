"""
generate_qtable_heatmap.py
==========================
Menghasilkan gambar Q-Table (25 State x 9 Aksi) dengan nilai Q
tercetak langsung di setiap sel. Kualitas 300 DPI untuk skripsi.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import os

# --- PATH ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
Q_FILE = os.path.join(BASE_DIR, "output", "v6_final", "Q_table.npy")
OUT_DIR = os.path.join(BASE_DIR, "output", "output_grafik_qtable")
os.makedirs(OUT_DIR, exist_ok=True)

# --- LABEL ---
ACTIONS = ["IDLE", "pH↑S", "pH↑L", "pH↓S", "pH↓L", "Nut S", "Nut L", "Air S", "Air L"]
STATES = [f"S{i+1}" for i in range(25)]

# Zona warna untuk setiap state (referensi Tabel 3.6)
ZONE_COLORS = {
    "Kritis Ekstrem": (0, 4, 20, 24),
    "Kritis": (1, 2, 3, 5, 9, 10, 14, 15, 19, 21, 22, 23),
    "Transisi": (6, 8, 16, 18),
    "Sub-Optimal": (7, 11, 13, 17),
    "Target (S13)": (12,),
}
ZONE_ROW_COLORS = {
    0: "#FFB3B3",
    4: "#FFB3B3",
    20: "#FFB3B3",
    24: "#FFB3B3",  # Kritis Ekstrem
    1: "#FFDDB3",
    2: "#FFDDB3",
    3: "#FFDDB3",
    5: "#FFDDB3",  # Kritis
    9: "#FFDDB3",
    10: "#FFDDB3",
    14: "#FFDDB3",
    15: "#FFDDB3",
    19: "#FFDDB3",
    21: "#FFDDB3",
    22: "#FFDDB3",
    23: "#FFDDB3",
    6: "#FFFAB3",
    8: "#FFFAB3",
    16: "#FFFAB3",
    18: "#FFFAB3",  # Transisi
    7: "#D4F5D4",
    11: "#D4F5D4",
    13: "#D4F5D4",
    17: "#D4F5D4",  # Sub-Optimal
    12: "#90EE90",  # Target
}


def generate():
    if not os.path.exists(Q_FILE):
        print(f"[ERROR] File tidak ditemukan: {Q_FILE}")
        return

    q = np.load(Q_FILE)  # shape (25, 9)

    # ============================================================
    # GAMBAR 1: Heatmap Penuh dengan Nilai Q
    # ============================================================
    fig, ax = plt.subplots(figsize=(16, 14))
    ax.set_aspect("equal")

    n_states, n_actions = q.shape
    q_min, q_max = q.min(), q.max()

    # Gambar setiap sel
    for row in range(n_states):
        for col in range(n_actions):
            val = q[row, col]

            # Warna latar berdasarkan nilai Q (normalisasi)
            norm = (val - q_min) / (q_max - q_min)
            # Warna: merah (rendah) → kuning → hijau (tinggi)
            if norm < 0.5:
                r, g, b = 1.0, norm * 2, 0.0
            else:
                r, g, b = 1.0 - (norm - 0.5) * 2, 1.0, 0.0

            rect = plt.Rectangle(
                [col, n_states - 1 - row],
                1,
                1,
                facecolor=(r, g, b, 0.75),
                edgecolor="white",
                linewidth=0.8,
            )
            ax.add_patch(rect)

            # Warna teks: hitam di latar terang, putih di gelap
            brightness = 0.299 * r + 0.587 * g + 0.114 * b
            txt_color = "black" if brightness > 0.4 else "white"

            # Cetak nilai Q
            ax.text(
                col + 0.5,
                n_states - 1 - row + 0.55,
                f"{val:.1f}",
                ha="center",
                va="center",
                fontsize=7.5,
                fontweight="bold",
                color=txt_color,
            )

            # Tandai nilai terbaik per state (aksi optimal)
            if col == np.argmax(q[row]):
                ax.text(
                    col + 0.5,
                    n_states - 1 - row + 0.22,
                    "★",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="#003366",
                )

    # Garis tepi state target (S13 = indeks 12)
    target_row_y = n_states - 1 - 12
    rect_target = plt.Rectangle(
        [0, target_row_y],
        n_actions,
        1,
        fill=False,
        edgecolor="#006400",
        linewidth=2.5,
        zorder=5,
    )
    ax.add_patch(rect_target)

    # Label sumbu X (Aksi)
    ax.set_xticks([i + 0.5 for i in range(n_actions)])
    ax.set_xticklabels(ACTIONS, fontsize=9, fontweight="bold")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("Aksi (Actions)", fontsize=11, fontweight="bold", labelpad=8)

    # Label sumbu Y (State)
    ax.set_yticks([i + 0.5 for i in range(n_states)])
    ax.set_yticklabels(list(reversed(STATES)), fontsize=9, fontweight="bold")
    ax.set_ylabel("State", fontsize=11, fontweight="bold", labelpad=8)

    # Warnai label state sesuai zona
    zone_label_colors = {}
    for idx in range(24):
        zone_label_colors[idx] = "#FFAAAA"  # default kritis
    for idx in (0, 4, 20, 24):
        zone_label_colors[idx] = "#FF4444"
    for idx in (1, 2, 3, 5, 9, 10, 14, 15, 19, 21, 22, 23):
        zone_label_colors[idx] = "#FF8800"
    for idx in (6, 8, 16, 18):
        zone_label_colors[idx] = "#BBBB00"
    for idx in (7, 11, 13, 17):
        zone_label_colors[idx] = "#228B22"
    zone_label_colors[12] = "#006400"

    for tick, label in zip(ax.get_yticklabels(), reversed(range(n_states))):
        tick.set_color(zone_label_colors.get(label, "black"))

    # Batas sumbu
    ax.set_xlim(0, n_actions)
    ax.set_ylim(0, n_states)
    ax.tick_params(left=False, top=False)

    # Judul
    ax.set_title(
        "Heatmap Nilai Q-Table\n(25 State × 9 Aksi | ★ = Aksi Optimal per State)",
        fontsize=13,
        fontweight="bold",
        pad=18,
    )

    # Legenda zona
    legend_items = [
        mpatches.Patch(facecolor="#FF4444", label="Kritis Ekstrem (−40)"),
        mpatches.Patch(facecolor="#FF8800", label="Kritis (−20)"),
        mpatches.Patch(facecolor="#EEEE00", label="Transisi (−2)"),
        mpatches.Patch(facecolor="#90EE90", label="Sub-Optimal (−1)"),
        mpatches.Patch(facecolor="#006400", label="Target S13 (+100)"),
    ]
    ax.legend(
        handles=legend_items,
        loc="lower right",
        bbox_to_anchor=(1.0, -0.08),
        ncol=5,
        fontsize=8.5,
        framealpha=0.9,
        title="Zona Reward",
        title_fontsize=9,
    )

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "qtable_heatmap_nilai.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[OK] Gambar Q-Table disimpan: {out_path}")

    # ============================================================
    # GAMBAR 2: Bar Chart — Aksi Terbaik per State
    # ============================================================
    best_actions = np.argmax(q, axis=1)
    best_qvals = np.max(q, axis=1)

    bar_colors = []
    for s in range(25):
        if s in (0, 4, 20, 24):
            bar_colors.append("#FF4444")
        elif s in (1, 2, 3, 5, 9, 10, 14, 15, 19, 21, 22, 23):
            bar_colors.append("#FF8800")
        elif s in (6, 8, 16, 18):
            bar_colors.append("#CCCC00")
        elif s in (7, 11, 13, 17):
            bar_colors.append("#90EE90")
        else:
            bar_colors.append("#006400")  # S13

    fig2, ax2 = plt.subplots(figsize=(14, 5))
    bars = ax2.bar(
        range(1, 26), best_qvals, color=bar_colors, edgecolor="black", alpha=0.85
    )

    # Label aksi terbaik di atas tiap bar
    for i, (bar, act_idx) in enumerate(zip(bars, best_actions)):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(best_qvals) * 0.01,
            ACTIONS[act_idx],
            ha="center",
            va="bottom",
            fontsize=7,
            fontweight="bold",
            rotation=45,
        )

    ax2.set_xticks(range(1, 26))
    ax2.set_xticklabels([f"S{i}" for i in range(1, 26)], fontsize=8)
    ax2.set_xlabel("ID State", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Nilai Q Terbaik (Max Q)", fontsize=11, fontweight="bold")
    ax2.set_title(
        "Nilai Q Maksimum dan Aksi Optimal untuk Setiap State (Model v6_final)",
        fontsize=12,
        fontweight="bold",
    )
    ax2.grid(axis="y", alpha=0.3)

    legend2 = [
        mpatches.Patch(facecolor="#FF4444", label="Kritis Ekstrem"),
        mpatches.Patch(facecolor="#FF8800", label="Kritis"),
        mpatches.Patch(facecolor="#CCCC00", label="Transisi"),
        mpatches.Patch(facecolor="#90EE90", label="Sub-Optimal"),
        mpatches.Patch(facecolor="#006400", label="Target S13"),
    ]
    ax2.legend(handles=legend2, fontsize=8.5, loc="upper left")

    plt.tight_layout()
    out_path2 = os.path.join(OUT_DIR, "qtable_best_action_per_state.png")
    plt.savefig(out_path2, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[OK] Gambar aksi optimal disimpan: {out_path2}")
    print(f"\n[SELESAI] Semua gambar tersimpan di: {OUT_DIR}")


if __name__ == "__main__":
    generate()
