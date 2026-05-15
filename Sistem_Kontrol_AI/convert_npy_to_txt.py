"""
convert_npy_to_txt.py
=====================
Membongkar file .npy hasil training v6_final menjadi file .txt 
agar bisa dibaca manual menggunakan Notepad.
"""

import numpy as np
import os

# --- KONFIGURASI PATH ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
V6_DIR     = os.path.join(BASE_DIR, "output", "v6_final")
OUT_DIR    = os.path.join(V6_DIR, "text_version")

os.makedirs(OUT_DIR, exist_ok=True)

# Daftar file yang akan dikonversi
FILES = [
    "Q_table.npy",
    "qmax_log.npy",
    "reward_log.npy",
    "state_visit.npy",
    "step_log.npy",
    "trajectory.npy",
    "alpha_log.npy",
    "action_count.npy"
]

def convert():
    print(f"\n[START] Mengonversi file .npy ke .txt di: {OUT_DIR}")
    print("-" * 50)
    
    for filename in FILES:
        npy_path = os.path.join(V6_DIR, filename)
        txt_path = os.path.join(OUT_DIR, filename.replace(".npy", ".txt"))
        
        if os.path.exists(npy_path):
            try:
                data = np.load(npy_path)
                
                # Cek dimensi data untuk menentukan format simpan
                if filename == "Q_table.npy":
                    # Simpan Q-Table dengan format tabel rapi
                    np.savetxt(txt_path, data, fmt='%.4f', delimiter='\t', 
                               header="IDLE\tUp_S\tUp_L\tDn_S\tDn_L\tNut_S\tNut_L\tAir_S\tAir_L")
                elif filename == "trajectory.npy":
                    # Trajectory biasanya besar, kita simpan per baris (Step, State, Action, Reward, Next_State)
                    np.savetxt(txt_path, data, fmt='%s', delimiter=', ')
                else:
                    # Untuk log 1D (reward, step, dll)
                    np.savetxt(txt_path, data, fmt='%.4f')
                
                print(f"  [OK] Berhasil: {filename} -> {os.path.basename(txt_path)}")
            except Exception as e:
                print(f"  [ERR] Gagal konversi {filename}: {e}")
        else:
            print(f"  [SKIP] File {filename} tidak ditemukan di folder v6_final.")

    print("-" * 50)
    print(f"[SELESAI] Silakan cek folder: {OUT_DIR}")

if __name__ == "__main__":
    convert()
