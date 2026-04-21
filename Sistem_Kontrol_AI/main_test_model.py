import numpy as np
import os
import time
from env_ph_ec import PhEcEnv


def main():
    # ==========================================
    # 0. KONFIGURASI VERSI (Otomatis dari env)
    # ==========================================
    env = PhEcEnv()
    VERSION = f"{env.ACTIVE_VERSION}_dataset_asli"
    path = f"../output/{VERSION}/Q_table.npy"

    if not os.path.exists(path):
        # Fallback untuk folder lama tanpa suffix _asli
        VERSION_OLD = f"{env.ACTIVE_VERSION}_dataset"
        path_old = f"../output/{VERSION_OLD}/Q_table.npy"
        if os.path.exists(path_old):
            VERSION = VERSION_OLD
            path = path_old

    if not os.path.exists(path):
        print(f"❌ File Q-Table tidak ditemukan di: {path}")
        print("Pastikan Anda sudah menjalankan training untuk versi ini.")
        return

    # 1. Load Q-Table
    Q = np.load(path)
    print(f"✅ Berhasil memuat Q-Table: {VERSION}")
    print("=" * 50)

    # 2. Inisialisasi Simulasi
    state, _ = env.reset()
    done = False
    total_reward = 0
    step_count = 0
    max_steps = 50

    action_names = [
        "Idle",
        "pH Up(S)",
        "pH Up(L)",
        "pH Down(S)",
        "pH Down(L)",
        "Nutrisi(S)",
        "Nutrisi(L)",
        "Air Baku(S)",
        "Air Baku(L)",
    ]

    print(f"{'Step':<5} | {'State':<5} | {'Aksi':<12} | {'Reward':<8} | {'Keterangan'}")
    print("-" * 65)

    while not done and step_count < max_steps:
        # Pilih aksi terbaik dari Q-Table (Greedy)
        action = np.argmax(Q[state])

        # Ambil informasi pH/EC indeks untuk tampilan
        ph_idx = state // 5
        ec_idx = state % 5

        # Execute step
        next_state, reward, done, _, _ = env.step(action)

        print(
            f"{step_count+1:<5} | {state:<5} | {action_names[action]:<12} | {reward:<8.1f} | pH Indeks:{ph_idx}, EC Indeks:{ec_idx}"
        )

        state = next_state
        total_reward += reward
        step_count += 1
        time.sleep(0.1)  # Efek dramatis biar bisa dibaca

    print("=" * 60)
    print(f"SIMULASI SELESAI DALAM {step_count} LANGKAH")
    print(f"TOTAL REWARD: {total_reward:.2f}")

    if done:
        print("🎯 TARGET TERCAPAI (Optimal State)!")
    else:
        print("⌛ BATAS LANGKAH TERCAPAI.")


if __name__ == "__main__":
    main()
