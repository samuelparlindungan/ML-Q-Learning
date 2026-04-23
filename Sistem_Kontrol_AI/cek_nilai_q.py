import numpy as np
import pandas as pd
import os


def main():
    # 1. Definisi Semua Versi Penelitian
    ALL_VERSIONS = ["v1_teori", "v2_dataset_asli", "v3_dataset_asli"]

    print("=" * 60)
    print("📋 BATCH REPORT GENERATOR: EXCEL Q-TABLE")
    print("=" * 60)

    for version in ALL_VERSIONS:
        path = f"../output/{version}/Q_table.npy"
        output_excel = f"../output/{version}/Laporan_Q_Table_Lengkap.xlsx"

        print(f"\n📂 MEMPROSES VERSI: {version.upper()}")

        # 1. Cek apakah file Q-table ada
        if not os.path.exists(path):
            print(f"⏩ Menyilang {version}: File Q-Table tidak ditemukan.")
            continue

        # 2. Load Q-Table
        try:
            q_table = np.load(path)  # Shape (25, 9)
            print(f"✅ Memuat Q-Table dari {path}...")
        except Exception as e:
            print(f"❌ Error saat memuat data {version}: {e}")
            continue

        # --- DEFINISI LABEL ---
        action_columns = [
            "0: Idle",
            "1: pH Up(S)",
            "2: pH Up(L)",
            "3: pH Down(S)",
            "4: pH Down(L)",
            "5: Nutrisi(S)",
            "6: Nutrisi(L)",
            "7: Air Baku(S)",
            "8: Air Baku(L)",
        ]

        ph_labels = [
            "VL (<5.5)",
            "Lo (5.5-5.8)",
            "Op (5.8-6.2)",
            "Hi (6.2-6.5)",
            "VH (>6.5)",
        ]
        ec_labels = [
            "VL (<0.8)",
            "Lo (0.8-1.1)",
            "Op (1.1-1.3)",
            "Hi (1.3-1.6)",
            "VH (>1.6)",
        ]

        # --- PEMROSESAN DATA ---
        data_list = []
        for s in range(25):
            ph_idx = s // 5
            ec_idx = s % 5
            state_desc = (
                f"State {s+1} | pH:{ph_labels[ph_idx]} | EC:{ec_labels[ec_idx]}"
            )
            row_values = q_table[s]
            best_action_idx = np.argmax(row_values)
            best_action_name = action_columns[best_action_idx]

            row_data = {"STATE ID": s + 1, "KONDISI LINGKUNGAN": state_desc}
            for i, act_name in enumerate(action_columns):
                row_data[act_name] = round(row_values[i], 2)
            row_data["KEPUTUSAN AGEN"] = best_action_name
            row_data["MAX Q-VALUE"] = round(row_values[best_action_idx], 2)
            data_list.append(row_data)

        # --- EKSPOR KE EXCEL ---
        df = pd.DataFrame(data_list)
        df.set_index("STATE ID", inplace=True)
        print(f"⏳ Menulis ke: {output_excel}")
        df.to_excel(output_excel)
        print(f"🎉 SUKSES untuk {version}.")

    print("\n" + "=" * 60)
    print("SELESAI! Semua laporan Excel telah diperbarui.")
    print("=" * 60)
    print("\nTips: Buka file Excel tersebut, lalu pilih semua sel dan klik dua kali")
    print("      pada batas kolom untuk merapikan lebar kolom secara otomatis.")


if __name__ == "__main__":
    main()
