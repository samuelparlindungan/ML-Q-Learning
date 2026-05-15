"""
visualize_state_transitions.py
==============================
Memvisualisasikan perpindahan State X ke State Y dari data real-time.
Menghasilkan Grafik Garis State dan Map Pergerakan Agent (Grid 5x5).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- KONFIGURASI ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
CSV_FILE = os.path.join(BASE_DIR, "output", "data_transisi_otomatis.csv")
OUT_DIR = os.path.join(BASE_DIR, "output", "output_grafik_transisi")

os.makedirs(OUT_DIR, exist_ok=True)


# Fungsi Konversi (Harus sama dengan main_auto_control.py)
def get_ph_idx(v):
    if v < 5.5:
        return 0
    elif v < 5.8:
        return 1
    elif v <= 6.2:
        return 2
    elif v <= 6.5:
        return 3
    else:
        return 4


def get_ec_idx(v):
    if v < 800:
        return 0
    elif v < 1100:
        return 1
    elif v <= 1300:
        return 2
    elif v <= 1600:
        return 3
    else:
        return 4


def get_state_id(ph, ec):
    return get_ph_idx(ph) * 5 + get_ec_idx(ec) + 1


# --- PROSES DATA ---
def generate():
    if not os.path.exists(CSV_FILE):
        print(f"[ERROR] File {CSV_FILE} tidak ditemukan!")
        return

    df = pd.read_csv(CSV_FILE)

    # Hitung State ID untuk setiap baris
    df["S_t"] = df.apply(lambda r: get_state_id(r["pH_St"], r["EC_St"]), axis=1)
    df["S_t1"] = df.apply(lambda r: get_state_id(r["pH_St+1"], r["EC_St+1"]), axis=1)

    steps = np.arange(1, len(df) + 1)
    states_path = df["S_t"].tolist()
    states_path.append(
        df["S_t1"].iloc[-1]
    )  # Tambah state terakhir setelah aksi terakhir
    path_steps = np.arange(1, len(states_path) + 1)

    # ------------------------------------------------------------
    # GAMBAR 1: GRAFIK GARIS TRANSISI (STATE vs STEP)
    # ------------------------------------------------------------
    plt.figure(figsize=(12, 5))
    plt.step(
        path_steps,
        states_path,
        where="post",
        color="#1A5276",
        linewidth=2,
        marker="o",
        markersize=4,
    )

    # Arsir zona target (State 13)
    plt.axhspan(12.5, 13.5, color="#27AE60", alpha=0.2, label="Zona Target (State 13)")

    plt.title(
        "Gambar 4.9 Grafik Perpindahan State Agen AI Per Langkah (Step)",
        fontweight="bold",
        pad=15,
    )
    plt.xlabel("Langkah Kendali (Step)")
    plt.ylabel("ID State (1 - 25)")
    plt.yticks(range(1, 26))
    plt.grid(True, alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "gambar_4_9_state_line_path.png"), dpi=300)
    print(f"[OK] Gambar 4.9 Selesai.")

    # ------------------------------------------------------------
    # GAMBAR 2: GRID TRANSISI (MAP PERGERAKAN)
    # ------------------------------------------------------------
    plt.figure(figsize=(8, 8))

    # Buat grid background
    grid = np.zeros((5, 5))
    plt.imshow(
        grid, cmap="Greys", extent=[-0.5, 4.5, -0.5, 4.5], origin="lower", alpha=0.1
    )

    # Gambar panah pergerakan
    for i in range(len(df)):
        p_start, e_start = get_ph_idx(df.loc[i, "pH_St"]), get_ec_idx(
            df.loc[i, "EC_St"]
        )
        p_end, e_end = get_ph_idx(df.loc[i, "pH_St+1"]), get_ec_idx(
            df.loc[i, "EC_St+1"]
        )

        # Tambahkan sedikit random offset agar panah tidak tumpang tindih jika balik ke state yang sama
        offset = np.random.uniform(-0.1, 0.1)

        plt.arrow(
            e_start + offset,
            p_start + offset,
            (e_end - e_start),
            (p_end - p_start),
            head_width=0.1,
            head_length=0.1,
            fc="#2980B9",
            ec="#2980B9",
            alpha=0.6,
            length_includes_head=True,
        )

    # Tandai Start dan End
    p_start_init, e_start_init = get_ph_idx(df.loc[0, "pH_St"]), get_ec_idx(
        df.loc[0, "EC_St"]
    )
    p_final, e_final = get_ph_idx(df.iloc[-1]["pH_St+1"]), get_ec_idx(
        df.iloc[-1]["EC_St+1"]
    )

    plt.scatter(
        e_start_init,
        p_start_init,
        color="red",
        s=100,
        label="Titik Mulai (Start)",
        zorder=5,
    )
    plt.scatter(
        e_final,
        p_final,
        color="green",
        s=150,
        marker="*",
        label="Titik Akhir (Finish)",
        zorder=5,
    )

    # Label Axis
    plt.xticks(range(5), ["S.Rendah", "Rendah", "Optimal", "Tinggi", "S.Tinggi"])
    plt.yticks(range(5), ["S.Rendah", "Rendah", "Optimal", "Tinggi", "S.Tinggi"])
    plt.xlabel("Indeks EC (Nutrisi)")
    plt.ylabel("Indeks pH")
    plt.title(
        "Gambar 4.10 Map Pergerakan Agen pada Grid State 5x5", fontweight="bold", pad=15
    )
    plt.grid(True, alpha=0.3)
    plt.legend()

    # Tambahkan nomor state di setiap kotak
    for p in range(5):
        for e in range(5):
            s_id = p * 5 + e + 1
            plt.text(e, p, f"S{s_id}", ha="center", va="center", alpha=0.3, fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "gambar_4_10_state_movement_map.png"), dpi=300)
    print(f"[OK] Gambar 4.10 Selesai.")
    print(f"\nGrafik disimpan di: {OUT_DIR}")


if __name__ == "__main__":
    generate()
