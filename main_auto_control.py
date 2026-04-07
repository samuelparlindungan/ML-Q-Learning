import paho.mqtt.client as mqtt
import time
import json
import os
import pandas as pd
from datetime import datetime

# ==========================================
# 0. VARIABEL TRACKING CSV
# ==========================================
CSV_AUTO = "output/data_transisi_otomatis.csv"
SESI_EKSPERIMEN = "AUTO_DEPLOY"
menunggu_st1 = False
last_st_ph = 0.0
last_st_ec = 0.0
last_action = -1
last_max_q = 0.0

def inisialisasi_csv():
    os.makedirs("output", exist_ok=True)
    if not os.path.exists(CSV_AUTO):
        df = pd.DataFrame(columns=[
            "Sesi_Eksperimen", "Aksi", "pH_St", "EC_St", 
            "pH_St+1", "EC_St+1", "Delta_pH", "Delta_EC", "Max_Q_Value", "Timestamp"
        ])
        df.to_csv(CSV_AUTO, index=False)

# ==========================================
# 1. KONFIGURASI MQTT & FILE AI
# ==========================================
MQTT_BROKER = "192.168.100.10"
MQTT_PORT = 1883
TOPIC_SENSOR = "hidroponik/sensor"
TOPIC_ACTION = "hidroponik/action"
TOPIC_STATUS = "hidroponik/status"

POLICY_FILE = "output/policy.json"
WAKTU_HOMOGENISASI = 180  # 3 Menit (180 detik) dalam satuan detik

# Status Sistem
status_sistem = "STANDBY"  # Bisa "STANDBY", "DOSING", "HOMOGENISASI"
waktu_selesai_homogenisasi = 0
policy_ai = {}


# ==========================================
# 2. LOAD KECERDASAN AI (POLICY.JSON)
# ==========================================
def load_ai_policy():
    global policy_ai
    if not os.path.exists(POLICY_FILE):
        print(
            f"? ERROR: File {POLICY_FILE} tidak ditemukan! Jalankan main_training.py dulu."
        )
        exit()
    with open(POLICY_FILE, "r") as f:
        policy_ai = json.load(f)
    print("[OK] Berhasil memuat kecerdasan AI dari policy.json!")


# ==========================================
# 3. FUNGSI DISKRITISASI (Tabel 3.1 & 3.2 B600)
# ==========================================
def get_ph_index(ph_val):
    if ph_val < 5.5:
        return 0
    elif 5.5 <= ph_val < 5.8:
        return 1
    elif 5.8 <= ph_val <= 6.2:
        return 2
    elif 6.2 < ph_val <= 6.5:
        return 3
    else:
        return 4


def get_ec_index(ec_val):
    if ec_val < 800:
        return 0
    elif 800 <= ec_val < 1100:
        return 1
    elif 1100 <= ec_val <= 1300:
        return 2
    elif 1300 < ec_val <= 1600:
        return 3
    else:
        return 4


# ==========================================
# 4. PEMETAAN AKSI & DURASI (Tabel 3.4 B600)
# ==========================================
def eksekusi_aksi(action_id):
    nama_aksi = ""
    if action_id == 0:
        nama_aksi = "IDLE"
        print("[IDLE] AKSI 0: IDLE (Kondisi sudah optimal. Menunggu Homogenisasi alami...)")
    elif action_id == 1:
        nama_aksi = "pH Up Short"
    elif action_id == 2:
        nama_aksi = "pH Up Long"
    elif action_id == 3:
        nama_aksi = "pH Down Short"
    elif action_id == 4:
        nama_aksi = "pH Down Long"
    elif action_id == 5:
        nama_aksi = "Nutrisi Short (A&B)"
    elif action_id == 6:
        nama_aksi = "Nutrisi Long (A&B)"
    elif action_id == 7:
        nama_aksi = "Air Baku Short"
    elif action_id == 8:
        nama_aksi = "Air Baku Long"

    # Publikasikan angka tunggal ke ESP32 Aktuator
    client.publish(TOPIC_ACTION, str(action_id))
    print(f"[ACTION] MENGIRIM PERINTAH AKSI {action_id} ({nama_aksi}) ke ESP32")
    return True


# ==========================================
# 5. HANDLER MQTT
# ==========================================
def on_connect(client, userdata, flags, rc):
    print("[MQTT] Terhubung ke MQTT Broker!")
    client.subscribe(TOPIC_SENSOR)
    client.subscribe(TOPIC_STATUS)


def on_message(client, userdata, msg):
    global status_sistem, waktu_selesai_homogenisasi
    global menunggu_st1, last_st_ph, last_st_ec, last_action, last_max_q

    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    # --- MENANGANI STATUS SELESAI DARI AKTUATOR ---
    if topic == TOPIC_STATUS and payload.strip() == "DONE":
        if status_sistem == "DOSING":
            print("[INFO] Pompa selesai! Memasuki Fase Homogenisasi (3 Menit)...")
            status_sistem = "HOMOGENISASI"
            waktu_selesai_homogenisasi = time.time() + WAKTU_HOMOGENISASI

    # --- MENANGANI SENSOR & KEPUTUSAN AI ---
    elif topic == TOPIC_SENSOR:
        # Jika sedang delay homogenisasi, abaikan dulu eksekusi aksi
        if status_sistem == "HOMOGENISASI":
            if time.time() >= waktu_selesai_homogenisasi:
                print(
                    "[OK] Homogenisasi Selesai. Sistem kembali STANDBY untuk State baru."
                )
                status_sistem = "STANDBY"
            return

        if status_sistem == "STANDBY":
            try:
                # Asumsi payload ESP32: {"ph": 6.1, "ec": 1150.0}
                data = json.loads(payload)
                pH_val = float(data.get("ph", data.get("pH", 0.0)))
                EC_val = float(data.get("ec", data.get("EC", 0.0)))

                # ----- FITUR SAFETY INTERLOCK (CEGAH SENSOR ERROR KABEL MENGAMBANG) -----
                if pH_val < 0.0 or pH_val > 14.0 or EC_val < 0.0 or EC_val > 5000.0:
                    print(f"[BAHAYA] Sensor Anomali Terdeteksi! (pH: {pH_val}, EC: {EC_val})")
                    print("[STOP] Agen menahan semua aksi pompa untuk mencegah kerusakan tandon.")
                    return
                # ------------------------------------------------------------------------

                # Cek apakah ini kemunculan pertama setelah Homogenisasi (Pencatatan St+1)
                if menunggu_st1:
                    delta_ph = round(pH_val - last_st_ph, 2)
                    delta_ec = round(EC_val - last_st_ec, 2)
                    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    df_baru = pd.DataFrame([{
                        "Sesi_Eksperimen": SESI_EKSPERIMEN,
                        "Aksi": last_action,
                        "pH_St": last_st_ph,
                        "EC_St": last_st_ec,
                        "pH_St+1": pH_val,
                        "EC_St+1": EC_val,
                        "Delta_pH": delta_ph,
                        "Delta_EC": delta_ec,
                        "Max_Q_Value": last_max_q,
                        "Timestamp": waktu_sekarang
                    }])
                    df_baru.to_csv(CSV_AUTO, mode='a', header=not os.path.exists(CSV_AUTO), index=False)
                    print(f"[LOG] CSV TERSIMPAN | Aksi: {last_action} | Delta pH: {delta_ph} | Delta EC: {delta_ec}")
                    menunggu_st1 = False

                # 1. Tentukan State saat ini
                ph_idx = get_ph_index(pH_val)
                ec_idx = get_ec_index(EC_val)
                state_index = ph_idx * 5 + ec_idx
                state_key = f"state_{state_index + 1}"

                # 2. Cari Aksi dari policy.json
                if state_key in policy_ai:
                    best_action = policy_ai[state_key]["best_action"]
                    max_q = policy_ai[state_key]["max_q"]
                    print(
                        f"[DATA] Sensor -> pH: {pH_val:.2f}, EC: {EC_val:.2f} | Memasuki {state_key}"
                    )
                    
                    # 3. Kunci State saat ini (St) untuk log masa depan
                    last_st_ph = pH_val
                    last_st_ec = EC_val
                    last_action = best_action
                    last_max_q = max_q
                    menunggu_st1 = True

                    # 4. Eksekusi
                    is_pumping = eksekusi_aksi(best_action)
                    if is_pumping:
                        status_sistem = "DOSING"

            except Exception as e:
                print(f"[ERROR] Parsing sensor data: {e}")


# ==========================================
# 6. LOOP UTAMA
# ==========================================
if __name__ == "__main__":
    print("=============================================")
    print("[SYSTEM] SISTEM KENDALI HIDROPONIK AI (Q-LEARNING)")
    print("=============================================")

    inisialisasi_csv()
    load_ai_policy()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[STOP] Sistem dihentikan manual oleh user.")
        client.disconnect()
