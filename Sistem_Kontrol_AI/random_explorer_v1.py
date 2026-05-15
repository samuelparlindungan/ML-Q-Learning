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
current_tx_id = ""  # ID unik untuk mencegah double-dosing


# ==========================================
# 3. CALLBACK MQTT
# ==========================================
def on_connect(client, userdata, flags, rc):
    print(f"✅ Terhubung ke Broker MQTT (RC: {rc})")
    client.subscribe(TOPIC_SENSOR)
    client.subscribe(TOPIC_STATUS)


def on_message(client, userdata, msg):
    global pompa_selesai, buffer_ph, buffer_ec
    payload = msg.payload.decode("utf-8")

    if msg.topic == TOPIC_STATUS:
        # Verifikasi apakah DONE ini milik perintah yang baru saja dikirim
        if payload == f"DONE:{current_tx_id}":
            pompa_selesai = True
            print(f"   [MQTT] Konfirmasi Diterima: {payload}")
        elif payload.startswith("DONE:"):
            print(f"   [MQTT] Abaikan konfirmasi lama: {payload}")

    elif msg.topic == TOPIC_SENSOR:
        try:
            data = json.loads(payload)
            ph = float(data.get("ph", data.get("pH", 0.0)))
            ec = float(data.get("ec", data.get("EC", 0.0)))
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
        if i % 15 == 0:
            print(f"   Sisa waktu sampling: {i}s")
        time.sleep(1)

    if len(buffer_ph) == 0:
        return None, None

    avg_ph = round(sum(buffer_ph) / len(buffer_ph), 2)
    avg_ec = round(sum(buffer_ec) / len(buffer_ec), 2)
    return avg_ph, avg_ec


def inisialisasi_csv(session_name):
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
        return 0
    try:
        df = pd.read_csv(CSV_FILENAME)
        if df.empty:
            return 0
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
    client.on_connect, client.on_message = on_connect, on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        print("\n" + "=" * 55)
        print("🤖   ROBOT EKSPLORASI ACAK (RELIABLE VERSION)   🤖")
        print("=" * 55)

        sesi_name = input("Masukkan Nama Sesi (Misal: Sesi_2): ")
        if not sesi_name:
            sesi_name = "Default_Session"

        CYCLES_TO_RUN = 50
        last_cycle = inisialisasi_csv(sesi_name)
        start_cycle = last_cycle + 1

        for cycle in range(start_cycle, CYCLES_TO_RUN + 1):
            print(f"\n🚀 >>> SIKLUS: {cycle}/{CYCLES_TO_RUN} <<<")

            # --- LANGKAH 1: STATE AWAL ---
            ph_st, ec_st = ambil_rata_rata(WAKTU_SAMP)
            if ph_st is None:
                print("❌ [ERROR] Sensor Offline! Berhenti.")
                break
            print(f"   [State St] pH: {ph_st} | EC: {ec_st}")

            # --- LANGKAH 2: AKSI ACAK DENGAN TXID ---
            aksi = random.randint(1, 8)
            current_tx_id = str(int(time.time()))[-6:]  # Unique ID
            payload = f"{aksi}:{current_tx_id}"

            # Pastikan Koneksi MQTT Aktif sebelum kirim
            if not client.is_connected():
                print("   ⚠️ [MQTT] Terputus! Menunggu koneksi kembali...")
                for _ in range(10):  # Tunggu max 10 detik
                    time.sleep(1)
                    if client.is_connected():
                        break

            success_sent = False
            for attempt in range(1, 5):  # Maks 4 kali percobaan
                if not client.is_connected():
                    print(f"   ❌ [MQTT] Percobaan {attempt} gagal: Broker Offline.")
                    time.sleep(2)
                    continue

                print(f"   [Action] Percobaan {attempt}/4: Kirim {payload}")
                pompa_selesai = False
                client.publish(TOPIC_ACTION, payload)

                start_wait = time.time()
                while not pompa_selesai:
                    if time.time() - start_wait > 20:  # Timeout 20 detik
                        print(f"   ⚠️ [TIMEOUT] Percobaan {attempt} gagal.")
                        break
                    time.sleep(0.5)

                if pompa_selesai:
                    success_sent = True
                    break

            if not success_sent:
                print(
                    "❌ [FAILED] Gagal mendapatkan konfirmasi hardware. Lewati siklus."
                )
                continue

            # --- LANGKAH 3: HOMOGENISASI ---
            print(f"   [Mixing] Homogenisasi {WAKTU_MIXING} detik...")
            time.sleep(WAKTU_MIXING)

            # --- LANGKAH 4: STATE AKHIR ---
            ph_st1, ec_st1 = ambil_rata_rata(WAKTU_SAMP)
            if ph_st1 is None:
                continue
            print(f"   [State St1] pH: {ph_st1} | EC: {ec_st1}")

            # --- LANGKAH 5: SIMPAN ---
            delta_ph, delta_ec = round(ph_st1 - ph_st, 2), round(ec_st1 - ec_st, 2)
            row = [
                sesi_name,
                cycle,
                ph_st,
                ec_st,
                aksi,
                ph_st1,
                ec_st1,
                delta_ph,
                delta_ec,
                datetime.now(),
            ]

            pd.DataFrame([row]).to_csv(
                CSV_FILENAME, mode="a", header=False, index=False
            )
            print(f"✅ [SUCCESS] Data Siklus {cycle} tersimpan.")

    except KeyboardInterrupt:
        print("\n🛑 Dihentikan manual.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Koneksi ditutup. File CSV Anda siap diolah!")
