import numpy as np
import pandas as pd
import os


def main():
    # Lokasi file Q-Table hasil training
    path = "output/Q_table.npy"
    output_excel = "output/Laporan_Q_Table_Lengkap.xlsx"

    # 1. Cek apakah file Q-table ada
    if not os.path.exists(path):
        print(f"❌ File {path} tidak ditemukan!")
        print("Jalankan 'main_training.py' terlebih dahulu.")
        return

    # 2. Load Q-Table
    q_table = np.load(path)  # Shape (25, 9)
    print(f"✅ Memuat Q-Table dari {path}...")

    # --- DEFINISI LABEL SESUAI DOKUMEN B600 ---

    # Definisi Aksi (Sesuai Tabel 3.4 B600)
    # Kolom Excel akan menggunakan nama ini
    action_columns = [
        "0: Idle",
        "1: pH Up (S)",
        "2: pH Up (L)",
        "3: pH Down (S)",
        "4: pH Down (L)",
        "5: Nutrisi (S)",
        "6: Nutrisi (L)",
        "7: Air Baku (S)",
        "8: Air Baku (L)",
    ]

    # Definisi Level untuk Label State (Sesuai Tabel 3.1 & 3.2)
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
        # Decode Index State (0-24) menjadi indeks pH dan EC (0-4)
        ph_idx = s // 5
        ec_idx = s % 5

        # Buat Nama State yang Deskriptif (Sesuai Tabel 3.3)
        state_desc = f"State {s+1} | pH:{ph_labels[ph_idx]} | EC:{ec_labels[ec_idx]}"

        # Ambil baris nilai Q untuk state ini
        row_values = q_table[s]

        # Cari Aksi Terbaik (Nilai Q Tertinggi)
        best_action_idx = np.argmax(row_values)
        best_value = row_values[best_action_idx]
        best_action_name = action_columns[best_action_idx]

        # Susun data untuk baris Excel
        row_data = {
            "STATE ID": s + 1,
            "KONDISI LINGKUNGAN": state_desc,
        }

        # Masukkan nilai Q per aksi ke kolom masing-masing
        for i, act_name in enumerate(action_columns):
            row_data[act_name] = round(row_values[i], 2)  # Dibulatkan 2 desimal

        # Tambahkan Kolom Analisis
        row_data["KEPUTUSAN AGEN"] = best_action_name
        row_data["MAX Q-VALUE"] = round(best_value, 2)

        data_list.append(row_data)

    # --- EKSPOR KE EXCEL ---
    df = pd.DataFrame(data_list)

    # Set Index agar rapi
    df.set_index("STATE ID", inplace=True)

    print("⏳ Sedang menulis ke file Excel...")

    # Menulis ke Excel
    df.to_excel(output_excel)

    print(f"🎉 SUKSES! File Excel tersimpan di:\n   >> {output_excel}")
    print("\nTips: Buka file Excel tersebut, lalu pilih semua sel dan klik dua kali")
    print("      pada batas kolom untuk merapikan lebar kolom secara otomatis.")


if __name__ == "__main__":
    main()
