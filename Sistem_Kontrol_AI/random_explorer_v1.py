import paho.mqtt.client as mqtt
import time
import pandas as pd
import os
import json
import random
from datetime import datetime

# ==========================================
# 1. KONFIGURASI MQTT & FILE
# ==========================================
MQTT_BROKER = "192.168.100.10"
MQTT_PORT = 1883
TOPIC_SENSOR = "hidroponik/sensor"
TOPIC_ACTION = "hidroponik/action"
TOPIC_STATUS = "hidroponik/status"

CSV_FILENAME = "../dataset_acak_qlearning.csv"
WAKTU_MIXING = 180  # 3 Menit jeda pelarutan
WAKTU_SAMP = 60  # 1 Menit pengambilan data per state (sesuai Skripsi)

# ==========================================
# 2. VARIABEL GLOBAL
# ==========================================
buffer_ph = []
buffer_ec = []
pompa_selesai = False


# ==========================================
# 3. CALLBACK MQTT
# ==========================================
def on_connect(client, userdata, flags, rc):
    print(f"Terhubung ke Broker dengan kode: {rc}")
    client.subscribe(TOPIC_SENSOR)
    client.subscribe(TOPIC_STATUS)


def on_message(client, userdata, msg):
    global pompa_selesai, buffer_ph, buffer_ec

    payload = msg.payload.decode("utf-8")

    if msg.topic == TOPIC_STATUS:
        if payload == "DONE":
            pompa_selesai = True

    elif msg.topic == TOPIC_SENSOR:
        try:
            data = json.loads(payload)
            # Menangani variasi penamaan key json dari ESP32
            ph = float(data.get("pH", data.get("ph", 0.0)))
            ec = float(data.get("EC", data.get("ec", 0.0)))
            buffer_ph.append(ph)
            buffer_ec.append(ec)
        except:
            pass


# ==========================================
# 4. FUNGSI HELPER
# ==========================================
def ambil_rata_rata(durasi_detik):
    global buffer_ph, buffer_ec
    buffer_ph.clear()
    buffer_ec.clear()

    print(f"   [Sampling] Mengambil data selama {durasi_detik} detik...")
    for i in range(durasi_detik, 0, -1):
        if i % 10 == 0:
            print(f"   Sisa waktu sampling: {i}s")
        time.sleep(1)

    if len(buffer_ph) == 0:
        return None, None

    avg_ph = round(sum(buffer_ph) / len(buffer_ph), 2)
    avg_ec = round(sum(buffer_ec) / len(buffer_ec), 2)
    return avg_ph, avg_ec


def inisialisasi_csv(session_name):
    """Mengecek file CSV dan mengembalikan nomor siklus terakhir dalam sesi tertentu."""
    if not os.path.exists(CSV_FILENAME):
        df = pd.DataFrame(
            columns=[
                "Sesi_Eksperimen",
                "Cycle",
                "pH_St",
                "EC_St",
                "Action",
                "pH_St1",
                "EC_St1",
                "Delta_pH",
                "Delta_EC",
                "Timestamp",
            ]
        )
        df.to_csv(CSV_FILENAME, index=False)
        print(f"File {CSV_FILENAME} baru berhasil dibuat.")
        return 0
    else:
        try:
            df = pd.read_csv(CSV_FILENAME)
            if df.empty:
                return 0
            # Filter berdasarkan Nama Sesi
            session_data = df[df["Sesi_Eksperimen"] == session_name]
            if session_data.empty:
                return 0
            return int(session_data["Cycle"].max())
        except:
            return 0


# ==========================================
# 5. PROGRAM UTAMA (RANDOM EXPLORER)
# ==========================================
if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        print("\n" + "=" * 50)
        print("     ROBOT EKSPLORASI ACAK (DATA COLLECTOR)     ")
        print("          Target: 50 Siklus per Sesi            ")
        print("=" * 50)

        sesi_eksperimen = input("Masukkan Nama Sesi (Misal: Eksplorasi_Sesi_2): ")
        if not sesi_eksperimen:
            sesi_eksperimen = "Default_Session"

        CYCLES_TO_RUN = 50  # Target siklus per sesi
        last_cycle_in_session = inisialisasi_csv(sesi_eksperimen)
        start_cycle = last_cycle_in_session + 1

        if last_cycle_in_session > 0:
            print(f"   [RESUME] Menemukan data Sesi '{sesi_eksperimen}'.")
            print(f"   Melanjutkan dari Siklus {start_cycle}...\n")
        else:
            print(f"   [NEW SESSION] Memulai Sesi '{sesi_eksperimen}' dari Siklus 1.\n")

        for cycle in range(start_cycle, CYCLES_TO_RUN + 1):
            print(f"\n>>> PROGRESS SESI: {cycle}/{CYCLES_TO_RUN} <<<")

            # --- LANGKAH 1: BACA STATE AWAL (St) ---
            ph_st, ec_st = ambil_rata_rata(WAKTU_SAMP)
            if ph_st is None:
                print("[ERROR] Data sensor tidak masuk. Cek ESP32!")
                break
            print(f"   [State St] pH: {ph_st} | EC: {ec_st}")

            # --- LANGKAH 2: PILIH AKSI ACAK (1-8) & KIRIM DENGAN RETRY ---
            aksi = random.randint(1, 8)

            # LOGIKA RETRY (Maksimal 3 Kali)
            success_sent = False
            for attempt in range(1, 4):
                print(f"   [Action] Percobaan {attempt}/3: Mengirim Aksi {aksi}...")
                pompa_selesai = False
                client.publish(TOPIC_ACTION, str(aksi))

                # Tunggu sinyal DONE dari Aktuator
                start_wait = time.time()
                while not pompa_selesai:
                    if time.time() - start_wait > 60:
                        print(
                            f"   [TIMEOUT] Aktuator tidak merespon (Percobaan {attempt})"
                        )
                        break
                    time.sleep(0.5)

                if pompa_selesai:
                    success_sent = True
                    break

                if attempt < 3:
                    print("   [RETRY] Mengirim ulang perintah...")

            if not success_sent:
                print(
                    f"   [SKIP] Siklus {cycle} dibatalkan setelah 3x percobaan gagal."
                )
                print("-" * 30)
                continue

            # --- LANGKAH 3: JEDA PELARUTAN (HOMOGENISASI) ---
            print(f"   [Mixing] Menunggu pelarutan selama {WAKTU_MIXING} detik...")
            time.sleep(WAKTU_MIXING)

            # --- LANGKAH 4: BACA STATE AKHIR (St+1) ---
            ph_st1, ec_st1 = ambil_rata_rata(WAKTU_SAMP)
            if ph_st1 is None:
                print("[ERROR] Data sensor St+1 hilang! Lewati.")
                continue
            print(f"   [State St1] pH: {ph_st1} | EC: {ec_st1}")

            # --- LANGKAH 5: HITUNG DELTA & SIMPAN ---
            delta_ph = round(ph_st1 - ph_st, 2)
            delta_ec = round(ec_st1 - ec_st, 2)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            row = {
                "Sesi_Eksperimen": sesi_eksperimen,
                "Cycle": cycle,
                "pH_St": ph_st,
                "EC_St": ec_st,
                "Action": aksi,
                "pH_St1": ph_st1,
                "EC_St1": ec_st1,
                "Delta_pH": delta_ph,
                "Delta_EC": delta_ec,
                "Timestamp": timestamp,
            }

            pd.DataFrame([row]).to_csv(
                CSV_FILENAME, mode="a", header=False, index=False
            )
            print(f"   [SUCCESS] Baris {cycle} tersimpan ke CSV.")
            print("-" * 30)

        print("\nTarget 50 siklus tercapai. Program selesai dengan aman.")

    except KeyboardInterrupt:
        print("\n\nProgram dihentikan paksa oleh pengguna.")
    except Exception as e:
        print(f"\nTerjadi kesalahan fatal: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Koneksi ditutup. File CSV Anda siap diolah!")
