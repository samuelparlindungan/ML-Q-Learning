"""
Skrip Pengekstrak Statistik Delta_pH & Delta_EC per Aksi
=========================================================
Menghitung Mean (μ) dan Std Dev (σ) dari dataset_acak_qlearning.csv
untuk digunakan sebagai parameter np.random.normal() di env_ph_ec.py
"""
import pandas as pd
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "dataset_acak_qlearning.csv"))

df = pd.read_csv(CSV_PATH)

# ============================================================
# DATA CLEANING (Sanity Check Filter)
# Berdasarkan instruksi: Buang anomali yang melanggar hukum fisika
# ============================================================
initial_count = len(df)

# 1. Filter Aksi 7 & 8 (Air Baku) yang justru menaikkan EC secara tidak wajar (> 50)
mask_baku_anomali = (df["Action"].isin([7, 8])) & (df["Delta_EC"] > 50)

# 2. Filter Aksi 1-4 (pH) yang menyebabkan lonjakan EC "liar" (> 500)
# (Catatan: pH Up memang menaikkan EC, tapi +600 adalah anomali sensor/homogenisasi)
mask_ph_anomali = (df["Action"].isin([1, 2, 3, 4])) & (df["Delta_EC"].abs() > 500)

# 3. Filter Delta pH yang mustahil secara fisik (> 2.0 dalam satu injeksi singkat)
mask_ph_absurd = df["Delta_pH"].abs() > 2.0

# Gabungkan semua filter
df_clean = df[~(mask_baku_anomali | mask_ph_anomali | mask_ph_absurd)].copy()

print(f"Total baris awal: {initial_count}")
print(f"Anomali dibuang: {initial_count - len(df_clean)} baris")
print(f"Data bersih tersedia: {len(df_clean)} baris")
print()

df = df_clean # Gunakan data yang sudah dikarantina untuk perhitungan μ dan σ
# ============================================================

# Tampilkan info dasar
sessions = df["Sesi_Eksperimen"].unique()
print(f"Sesi tersedia: {list(sessions)}")
print()

# ============================================================
# HITUNG PER SESI (untuk perbandingan)
# ============================================================
for sesi in sessions:
    df_sesi = df[df["Sesi_Eksperimen"] == sesi]
    print(f"{'='*60}")
    print(f"  SESI: {sesi} ({len(df_sesi)} siklus)")
    print(f"{'='*60}")
    for action_id in range(1, 9):
        subset = df_sesi[df_sesi["Action"] == action_id]
        n = len(subset)
        if n == 0:
            continue
        mu_ph = subset["Delta_pH"].mean()
        sigma_ph = subset["Delta_pH"].std() if n > 1 else 0.0
        mu_ec = subset["Delta_EC"].mean()
        sigma_ec = subset["Delta_EC"].std() if n > 1 else 0.0
        print(f"  Aksi {action_id}: n={n:2d} | "
              f"d_pH: mean={mu_ph:+7.3f}, std={sigma_ph:6.3f} | "
              f"d_EC: mean={mu_ec:+8.2f}, std={sigma_ec:7.2f}")
    print()

# ============================================================
# HITUNG GABUNGAN SEMUA SESI (untuk env_ph_ec.py)
# ============================================================
print(f"\n{'#'*60}")
print(f"  GABUNGAN SEMUA SESI (UNTUK env_ph_ec.py)")
print(f"{'#'*60}")

ACTION_NAMES = {
    1: "pH Up Short",
    2: "pH Up Long",
    3: "pH Down Short",
    4: "pH Down Long",
    5: "Nutrisi Short",
    6: "Nutrisi Long",
    7: "Air Baku Short",
    8: "Air Baku Long",
}

print("\n# Copy-paste ke env_ph_ec.py:")
print("# ============================================================")
for action_id in range(1, 9):
    subset = df[df["Action"] == action_id]
    n = len(subset)
    if n == 0:
        print(f"# Aksi {action_id} ({ACTION_NAMES[action_id]}): TIDAK ADA DATA")
        continue
    mu_ph = subset["Delta_pH"].mean()
    sigma_ph = subset["Delta_pH"].std() if n > 1 else 0.01
    mu_ec = subset["Delta_EC"].mean()
    sigma_ec = subset["Delta_EC"].std() if n > 1 else 1.0
    
    # Clamp sigma minimum agar tidak nol
    sigma_ph = max(sigma_ph, 0.01)
    sigma_ec = max(sigma_ec, 1.0)
    
    print(f"\n# Aksi {action_id}: {ACTION_NAMES[action_id]} (n={n} sampel)")
    print(f"# delta_ph = np.random.normal({mu_ph:+.4f}, {sigma_ph:.4f})")
    print(f"# delta_ec = np.random.normal({mu_ec:+.2f}, {sigma_ec:.2f})")

# ============================================================
# HITUNG KHUSUS SESI 3 (sebagai perbandingan)
# ============================================================
print(f"\n\n{'#'*60}")
print(f"  KHUSUS SESI 3 (Golden Dataset)")
print(f"{'#'*60}")

df_s3 = df[df["Sesi_Eksperimen"] == "Eksplorasi_Sesi_3"]
if len(df_s3) > 0:
    for action_id in range(1, 9):
        subset = df_s3[df_s3["Action"] == action_id]
        n = len(subset)
        if n == 0:
            print(f"\n# Aksi {action_id}: {ACTION_NAMES[action_id]} - TIDAK ADA DATA di Sesi 3")
            continue
        mu_ph = subset["Delta_pH"].mean()
        sigma_ph = subset["Delta_pH"].std() if n > 1 else 0.01
        mu_ec = subset["Delta_EC"].mean()
        sigma_ec = subset["Delta_EC"].std() if n > 1 else 1.0
        sigma_ph = max(sigma_ph, 0.01)
        sigma_ec = max(sigma_ec, 1.0)
        
        print(f"\n# Aksi {action_id}: {ACTION_NAMES[action_id]} (n={n})")
        print(f"# delta_ph = np.random.normal({mu_ph:+.4f}, {sigma_ph:.4f})")
        print(f"# delta_ec = np.random.normal({mu_ec:+.2f}, {sigma_ec:.2f})")
