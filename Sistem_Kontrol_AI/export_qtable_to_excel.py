"""
export_qtable_to_excel.py
=========================
Mengekspor Q-Table (State-Action Pairs) dari model v6_final
menjadi file CSV yang bisa langsung dibuka di Excel.
"""

import numpy as np
import pandas as pd
import os

# --- PATH ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
Q_FILE     = os.path.join(BASE_DIR, "output", "v6_final", "Q_table.npy")
SAVE_PATH  = os.path.join(BASE_DIR, "output", "Tabel_Q_Values_v6_final.csv")

# Nama Aksi sesuai Tabel 3.4 Skripsi
ACTIONS = [
    "0_IDLE", 
    "1_pH_Up_S", "2_pH_Up_L", 
    "3_pH_Down_S", "4_pH_Down_L", 
    "5_Nutrisi_S", "6_Nutrisi_L", 
    "7_Air_Baku_S", "8_Air_Baku_L"
]

def export():
    if not os.path.exists(Q_FILE):
        print(f"[ERROR] File {Q_FILE} tidak ditemukan!")
        return

    # Load Q-Table
    q_table = np.load(Q_FILE) # (25, 9)
    
    # Buat DataFrame
    df = pd.DataFrame(q_table, columns=ACTIONS)
    
    # Tambahkan kolom ID State di awal
    df.insert(0, "ID_State", [f"State_{i+1}" for i in range(25)])
    
    # Tambahkan kolom Best Action (Aksi dengan Q tertinggi)
    df["Best_Action_Index"] = np.argmax(q_table, axis=1)
    df["Best_Action_Name"] = [ACTIONS[i] for i in df["Best_Action_Index"]]

    # Simpan ke CSV dengan format Excel Indonesia (Semicolon separator, Comma decimal)
    # Ini agar Excel tidak salah baca titik desimal menjadi ribuan
    df.to_csv(SAVE_PATH, index=False, sep=';', decimal=',')
    
    print("\n" + "="*40)
    print("HASIL EKSPOR Q-TABLE")
    print("="*40)
    print(f"LOKASI: {SAVE_PATH}")
    print(f"JUMLAH: 25 State x 9 Aksi")
    print("-" * 40)
    print(df.head()) # Tampilkan 5 baris pertama
    print("="*40)
    print("\nBapak bisa langsung buka file tersebut dengan Microsoft Excel.")

if __name__ == "__main__":
    export()
