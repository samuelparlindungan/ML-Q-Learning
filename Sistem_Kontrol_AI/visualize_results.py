import pandas as pd
import matplotlib.pyplot as plt
import os

# --- KONFIGURASI PATH ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "output", "data_transisi_otomatis.csv"))
SAVE_DIR_LOCAL = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "output", "graphs"))
SAVE_DIR_BACKUP = r"D:\D Back Up\Semester 8\TA 2\AI"

# Buat direktori jika belum ada
os.makedirs(SAVE_DIR_LOCAL, exist_ok=True)
if os.path.exists(os.path.dirname(SAVE_DIR_BACKUP)):
    os.makedirs(SAVE_DIR_BACKUP, exist_ok=True)

def generate_plots():
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] File {CSV_PATH} tidak ditemukan! Pastikan sistem kontrol sudah dijalankan.")
        return

    df = pd.read_csv(CSV_PATH)
    steps = range(1, len(df) + 1)

    # 1. Grafik EC vs Step
    plt.figure(figsize=(12, 6))
    plt.plot(steps, df['EC_St+1'], marker='o', linestyle='-', color='#1f77b4', label='EC Aktual')
    plt.axhline(y=800, color='green', linestyle='--', alpha=0.6, label='Batas Bawah Optimal (800)')
    plt.axhline(y=1500, color='green', linestyle='--', alpha=0.6, label='Batas Atas Optimal (1500)')
    plt.fill_between(steps, 800, 1500, color='green', alpha=0.1, label='Zona Optimal')
    plt.xlabel('Langkah (Step) Keputusan')
    plt.ylabel('EC (µS/cm)')
    plt.title('Respon Nilai EC terhadap Aksi Kontrol Agen RL', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_DIR_LOCAL, 'plot_ec.png'), dpi=300)
    if os.path.exists(SAVE_DIR_BACKUP):
        plt.savefig(os.path.join(SAVE_DIR_BACKUP, 'plot_ec.png'), dpi=300)
    plt.close()

    # 2. Grafik pH vs Step
    plt.figure(figsize=(12, 6))
    plt.plot(steps, df['pH_St+1'], marker='s', linestyle='-', color='#d62728', label='pH Aktual')
    plt.axhline(y=5.5, color='green', linestyle='--', alpha=0.6, label='Batas Bawah Optimal (5.5)')
    plt.axhline(y=6.5, color='green', linestyle='--', alpha=0.6, label='Batas Atas Optimal (6.5)')
    plt.fill_between(steps, 5.5, 6.5, color='green', alpha=0.1, label='Zona Optimal')
    plt.xlabel('Langkah (Step) Keputusan')
    plt.ylabel('Nilai pH')
    plt.title('Respon Nilai pH terhadap Aksi Kontrol Agen RL', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_DIR_LOCAL, 'plot_ph.png'), dpi=300)
    if os.path.exists(SAVE_DIR_BACKUP):
        plt.savefig(os.path.join(SAVE_DIR_BACKUP, 'plot_ph.png'), dpi=300)
    plt.close()

    # 3. Grafik Reward per Step
    plt.figure(figsize=(12, 6))
    colors = ['#2ca02c' if r > 0 else '#ff7f0e' for r in df['Reward']]
    plt.bar(steps, df['Reward'], color=colors, alpha=0.8, label='Reward')
    plt.xlabel('Langkah (Step) Keputusan')
    plt.ylabel('Nilai Reward')
    plt.title('Akumulasi Reward Agen RL per Langkah Keputusan', fontsize=14, fontweight='bold')
    plt.axhline(y=0, color='black', linewidth=0.8)
    plt.grid(axis='y', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_DIR_LOCAL, 'plot_reward.png'), dpi=300)
    if os.path.exists(SAVE_DIR_BACKUP):
        plt.savefig(os.path.join(SAVE_DIR_BACKUP, 'plot_reward.png'), dpi=300)
    plt.close()

    print(f"\n[SUKSES] 3 Grafik telah berhasil di-generate!")
    print(f"LOKASI 1: {SAVE_DIR_LOCAL}")
    if os.path.exists(SAVE_DIR_BACKUP):
        print(f"LOKASI 2: {SAVE_DIR_BACKUP}")

if __name__ == "__main__":
    generate_plots()
