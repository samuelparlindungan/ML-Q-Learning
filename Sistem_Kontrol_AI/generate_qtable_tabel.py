"""
generate_qtable_tabel.py
========================
Menampilkan Q-Table (25 State × 9 Aksi) sebagai TABEL BERSIH,
tanpa heatmap gradien. Warna latar per baris = zona reward.
Nilai aksi optimal per state dicetak tebal + bintang.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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


# Zona per indeks state (0-based)
def get_zone(idx):
    if idx in (0, 4, 20, 24):
        return "ekstrem"
    if idx in (1, 2, 3, 5, 9, 10, 14, 15, 19, 21, 22, 23):
        return "kritis"
    if idx in (6, 8, 16, 18):
        return "transisi"
    if idx in (7, 11, 13, 17):
        return "suboptimal"
    if idx == 12:
        return "target"
    return "kritis"


ZONE_BG = {
    "ekstrem": "#FFD0D0",
    "kritis": "#FFE9CC",
    "transisi": "#FFFACC",
    "suboptimal": "#D8F5D8",
    "target": "#B2EDB2",
}
ZONE_LABEL_COLOR = {
    "ekstrem": "#CC0000",
    "kritis": "#CC6600",
    "transisi": "#999900",
    "suboptimal": "#1A7A1A",
    "target": "#005500",
}


def generate():
    if not os.path.exists(Q_FILE):
        print(f"[ERROR] File tidak ditemukan: {Q_FILE}")
        return

    q = np.load(Q_FILE)  # shape (25, 9)
    n_states, n_actions = q.shape

    # ============================================================
    # GAMBAR: Tabel Bersih Q-Table
    # ============================================================
    fig, ax = plt.subplots(figsize=(15, 13))
    ax.axis("off")

    n_cols = n_actions + 1  # +1 untuk kolom State ID
    n_rows = n_states + 1  # +1 untuk header

    col_w = 1.0 / n_cols
    row_h = 1.0 / n_rows

    # --- Header ---
    headers = ["State"] + ACTIONS
    for c, hdr in enumerate(headers):
        x = c * col_w
        y = 1.0 - row_h
        rect = plt.Rectangle(
            (x, y),
            col_w,
            row_h,
            transform=ax.transAxes,
            clip_on=False,
            facecolor="#2C3E50",
            edgecolor="white",
            linewidth=1.0,
        )
        ax.add_patch(rect)
        ax.text(
            x + col_w / 2,
            y + row_h / 2,
            hdr,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="white",
            clip_on=False,
        )

    # --- Baris Data ---
    for row in range(n_states):
        zone = get_zone(row)
        bg = ZONE_BG[zone]
        lbl_c = ZONE_LABEL_COLOR[zone]
        best_c = np.argmax(q[row])

        y = 1.0 - row_h * (row + 2)  # row+2 karena header di baris 0

        for col in range(n_cols):
            x = col * col_w

            # Warna sel
            if col == 0:
                cell_bg = "#ECF0F1"
            else:
                # Kolom aksi optimal punya latar sedikit lebih hijau
                cell_bg = "#C8F0C8" if (col - 1) == best_c else bg

            rect = plt.Rectangle(
                (x, y),
                col_w,
                row_h,
                transform=ax.transAxes,
                clip_on=False,
                facecolor=cell_bg,
                edgecolor="white",
                linewidth=0.8,
            )
            ax.add_patch(rect)

            if col == 0:
                # Label state
                ax.text(
                    x + col_w / 2,
                    y + row_h / 2,
                    STATES[row],
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    fontweight="bold",
                    color=lbl_c,
                    clip_on=False,
                )
            else:
                act_idx = col - 1
                val = q[row, act_idx]
                is_best = act_idx == best_c

                txt = f"{val:.1f}"
                fw = "bold" if is_best else "normal"
                tc = "#004400" if is_best else "#222222"

                ax.text(
                    x + col_w / 2,
                    y + row_h * 0.65,
                    txt,
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    fontweight=fw,
                    color=tc,
                    clip_on=False,
                )

                if is_best:
                    ax.text(
                        x + col_w / 2,
                        y + row_h * 0.25,
                        "★",
                        transform=ax.transAxes,
                        ha="center",
                        va="center",
                        fontsize=6.5,
                        color="#005500",
                        clip_on=False,
                    )

    # --- Garis tepi tabel luar ---
    border = plt.Rectangle(
        (0, 0),
        1.0,
        1.0,
        transform=ax.transAxes,
        clip_on=False,
        fill=False,
        edgecolor="#2C3E50",
        linewidth=1.5,
    )
    ax.add_patch(border)

    # --- Judul ---
    fig.suptitle(
        "Tabel Nilai Q-Table  (25 State × 9 Aksi)\n"
        "★ = Aksi Optimal per State  |  Latar hijau = kolom aksi terbaik",
        fontsize=11,
        fontweight="bold",
        y=0.98,
    )

    # --- Legenda zona ---
    legend_items = [
        mpatches.Patch(
            facecolor=ZONE_BG["ekstrem"],
            edgecolor="#999",
            label="Kritis Ekstrem (R = −40)",
        ),
        mpatches.Patch(
            facecolor=ZONE_BG["kritis"], edgecolor="#999", label="Kritis (R = −20)"
        ),
        mpatches.Patch(
            facecolor=ZONE_BG["transisi"], edgecolor="#999", label="Transisi (R = −2)"
        ),
        mpatches.Patch(
            facecolor=ZONE_BG["suboptimal"],
            edgecolor="#999",
            label="Sub-Optimal (R = −1)",
        ),
        mpatches.Patch(
            facecolor=ZONE_BG["target"], edgecolor="#999", label="Target S13 (R = +100)"
        ),
        mpatches.Patch(
            facecolor="#C8F0C8", edgecolor="#999", label="Aksi Optimal (kolom)"
        ),
    ]
    fig.legend(
        handles=legend_items,
        loc="lower center",
        ncol=6,
        fontsize=7.5,
        framealpha=0.9,
        bbox_to_anchor=(0.5, 0.00),
        title="Keterangan Zona",
        title_fontsize=8,
    )

    plt.subplots_adjust(top=0.95, bottom=0.06)

    out_path = os.path.join(OUT_DIR, "qtable_tabel_bersih.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[OK] Tabel Q bersih disimpan: {out_path}")
    print(f"[SELESAI] Output: {OUT_DIR}")


if __name__ == "__main__":
    generate()
