import paho.mqtt.client as mqtt
import time
import pandas as pd
import os
import json
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning)

### ==========================================
### 1. KONFIGURASI MQTT & FILE
### ==========================================
MQTT_BROKER = "192.168.100.10"
MQTT_PORT = 1883
TOPIC_SENSOR = "hidroponik/sensor"
TOPIC_ACTION = "hidroponik/action"
TOPIC_STATUS = "hidroponik/status"

CSV_FILENAME = "../data_transisi_manual.csv"

### ==========================================
### 2. VARIABEL GLOBAL
### ==========================================
buffer_ph_st = []
buffer_ec_st = []
buffer_ph_st1 = []
buffer_ec_st1 = []

fase_st1_aktif = False
pompa_selesai = False

### WAKTU HOMOGENISASI AKTUAL (3 Menit)
WAKTU_HOMOGENISASI = 180


### ==========================================
### 3. FUNGSI MQTT
### ==========================================
def on_connect(client, userdata, flags, rc):
    print("Terhubung ke MQTT Broker!")
    client.subscribe(TOPIC_SENSOR)
    client.subscribe(TOPIC_STATUS)


def on_message(client, userdata, msg):
    global buffer_ph_st, buffer_ec_st, buffer_ph_st1, buffer_ec_st1
    global fase_st1_aktif, pompa_selesai

    if msg.topic == TOPIC_STATUS:
        payload = msg.payload.decode("utf-8")
        if payload == "DONE":
            pompa_selesai = True

    elif msg.topic == TOPIC_SENSOR:
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            ph = float(data.get("pH", data.get("ph", data.get("Ph", 0.0))))
            ec = float(data.get("EC", data.get("ec", data.get("Ec", 0.0))))

            if not fase_st1_aktif:
                buffer_ph_st.append(ph)
                buffer_ec_st.append(ec)
            else:
                buffer_ph_st1.append(ph)
                buffer_ec_st1.append(ec)
        except Exception as e:
            pass


### ==========================================
### 4. INISIALISASI CSV DENGAN HEADER TIMESTAMP
### ==========================================
def inisialisasi_csv():
    if not os.path.exists(CSV_FILENAME):
        df = pd.DataFrame(
            columns=[
                "Sesi_Eksperimen",
                "Aksi",
                "pH_St",
                "EC_St",
                "pH_St+1",
                "EC_St+1",
                "Delta_pH",
                "Delta_EC",
                "Timestamp",
            ]
        )
        df.to_csv(CSV_FILENAME, index=False)


### ==========================================
### 5. PROGRAM UTAMA
### ==========================================
if __name__ == "__main__":
    inisialisasi_csv()

    print("==================================================")
    print("   PROGRAM PENGUJIAN GANGGUAN (DISTURBANCE TEST)  ")
    print("==================================================")
    sesi_eksperimen = input("Masukkan Nama Sesi (Misal: Normal_15L / Gangguan_1L): ")

    # Setup MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    try:
        while True:
            print("\n==================================================")
            pilihan = input("Ketik 'q' untuk berhenti, atau Enter untuk lanjut: ")
            if pilihan.lower() == "q":
                break

            # --- LANGKAH 1: KUMPULKAN St ---
            print("\nMengumpulkan data State Awal (St) selama 60 DETIK...")
            fase_st1_aktif = False
            buffer_ph_st.clear()
            buffer_ec_st.clear()

            time.sleep(60)

            if len(buffer_ph_st) == 0:
                print("PERINGATAN: Tidak ada data masuk! Periksa koneksi ESP32.")
                continue

            ph_st = round(sum(buffer_ph_st) / len(buffer_ph_st), 2)
            ec_st = round(sum(buffer_ec_st) / len(buffer_ec_st), 2)

            print(
                f">>> [LOCKED St] pH: {ph_st} | EC: {ec_st} | Sampel: {len(buffer_ph_st)} data <<<"
            )

            # --- LANGKAH 2: EKSEKUSI AKSI ---
            print("\nPilih Aksi Pompa (0-8):")
            print("1/2: pH Up (S/L)   | 5/6: Nutrisi (S/L)")
            print("3/4: pH Down (S/L) | 7/8: Air Baku (S/L)")
            print("0:   Lewati (Skip)")

            aksi = input("Masukkan Angka Aksi: ")
            if not aksi.isdigit() or int(aksi) < 0 or int(aksi) > 8:
                print("Aksi tidak valid! Mengulang proses.")
                continue

            pompa_selesai = False
            client.publish(TOPIC_ACTION, str(aksi))
            print(f"\nPerintah Aksi {aksi} dikirim. Menunggu eksekusi hardware...")

            # Timeout 30 detik agar tidak macet jika Aktuator mati
            timeout_detik = 30
            start_wait = time.time()
            while not pompa_selesai:
                if time.time() - start_wait > timeout_detik:
                    print("\n[ERROR] ESP32 Aktuator Timeout (Tidak membalas 'DONE')!")
                    break
                time.sleep(0.5)

            if not pompa_selesai:
                print("Gagal mengeksekusi aksi. Silakan cek power Aktuator.")
                continue

            # --- LANGKAH 3: HOMOGENISASI ---
            print(
                f"Hardware selesai! Menunggu homogenisasi {WAKTU_HOMOGENISASI} detik (3 Menit)..."
            )
            for i in range(WAKTU_HOMOGENISASI, 0, -1):
                print(f"Sisa waktu pelarutan: {i} detik...  ", end="\r")
                time.sleep(1)
            print("\nHomogenisasi selesai.")

            # --- LANGKAH 4: KUMPULKAN St+1 ---
            print("\nMengumpulkan data State Baru (St+1) selama 60 DETIK...")
            fase_st1_aktif = True
            buffer_ph_st1.clear()
            buffer_ec_st1.clear()

            time.sleep(60)

            if len(buffer_ph_st1) == 0:
                print(
                    "PERINGATAN: Tidak ada data sensor St+1 masuk! Data tidak disimpan."
                )
                continue

            ph_st1 = round(sum(buffer_ph_st1) / len(buffer_ph_st1), 2)
            ec_st1 = round(sum(buffer_ec_st1) / len(buffer_ec_st1), 2)

            print(
                f">>> [LOCKED St+1] pH: {ph_st1} | EC: {ec_st1} | Sampel: {len(buffer_ph_st1)} data <<<"
            )

            # --- LANGKAH 5: SIMPAN DATA DENGAN TIMESTAMP ---
            delta_ph = round(ph_st1 - ph_st, 2)
            delta_ec = round(ec_st1 - ec_st, 2)

            waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            df_baru = pd.DataFrame(
                [
                    {
                        "Sesi_Eksperimen": sesi_eksperimen,
                        "Aksi": int(aksi),
                        "pH_St": ph_st,
                        "EC_St": ec_st,
                        "pH_St+1": ph_st1,
                        "EC_St+1": ec_st1,
                        "Delta_pH": delta_ph,
                        "Delta_EC": delta_ec,
                        "Timestamp": waktu_sekarang,
                    }
                ]
            )

            df_baru.to_csv(
                CSV_FILENAME,
                mode="a",
                header=not os.path.exists(CSV_FILENAME),
                index=False,
            )
            print(
                f"\n[SUKSES] Data tersimpan! (Delta pH: {delta_ph} | Delta EC: {delta_ec}) pada {waktu_sekarang}\n"
            )

    except KeyboardInterrupt:
        print("\n\nProgram dihentikan (Ctrl+C).")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Koneksi MQTT ditutup. Selamat mengambil data!")
