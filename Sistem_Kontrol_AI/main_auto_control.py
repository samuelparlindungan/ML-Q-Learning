import paho.mqtt.client as mqtt
import time, json, os, pandas as pd
import csv
from datetime import datetime
from env_ph_ec import get_ph_idx, get_ec_idx, get_reward

# ==========================================
# 0. KONFIGURASI SISTEM
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MQTT_BROKER, MQTT_PORT = "192.168.100.10", 1883
TOPICS = {
    "sensor": "hidroponik/sensor",
    "action": "hidroponik/action",
    "status": "hidroponik/status",
}
# GUNAKAN v6_final UNTUK HASIL OPTIMAL (ANTI-HACKING)
VERSION_LOAD = "v6_final"
CSV_AUTO = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "output", "data_transisi_otomatis.csv")
)
POLICY_FILE = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "output", VERSION_LOAD, "policy.json")
)
LOG_FILE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "output", "system_log.csv"))
# --- RIWAYAT MODE PENGOPERASIAN ---
# MAX_ACTIONS = 0   # v1: Tanpa Batas (Jangka Panjang)
MAX_ACTIONS = 50  # v2: Uji Keandalan (Terbatas 50 Aksi)

WAKTU_HOMO = 180  # v2: 3 Menit (Hasil Eksperimen Tandon 15L)

WAKTU_SAMPLING = 60  # v2: 1 Menit (Optimal untuk Real-time)

# State Tracking
status = "SAMPLING"  # Mulai dengan sampling data awal
waktu_homo_end = 0
waktu_sampling_end = time.time() + WAKTU_SAMPLING
waktu_resend_next = 0  # Untuk Retry Logic
current_tx_id = ""  # ID unik untuk siklus ini
policy_ai = {}
sampling_buffer = {"ph": [], "ec": []}
tracking = {
    "wait_st1": False,
    "st_ph": 0.0,
    "st_ec": 0.0,
    "act": -1,
    "q": 0.0,
    "total_actions": 0,
}

# --- KONFIGURASI SAFETY (True = Aktif, False = Bypass/Mati) ---
# Sesuai kondisi bapak: T1 rusak (False), T2-T5 oke (True)
SAFETY_SWITCH = [False, True, True, True, True]  # [T1, T2, T3, T4, T5]

# Mapping Aksi
ACTIONS = {
    0: "IDLE",
    1: "pH Up S",
    2: "pH Up L",
    3: "pH Down S",
    4: "pH Down L",
    5: "Nutrisi S",
    6: "Nutrisi L",
    7: "Air S",
    8: "Air L",
}


# ==========================================
# 1. FUNGSI PEMBANTU
# ==========================================
def write_log(event_type, topic, detail=""):
    """Tulis satu baris log ke file CSV."""
    file_exists = os.path.isfile(LOG_FILE)
    # Pastikan direktori output ada
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "event_type", "topic", "detail"])
        writer.writerow([datetime.now().isoformat(), event_type, topic, detail])


def get_ph_idx(v):
    return 0 if v < 5.5 else 1 if v < 5.8 else 2 if v <= 6.2 else 3 if v <= 6.5 else 4


def get_ec_idx(v):
    return (
        0 if v < 800 else 1 if v < 1100 else 2 if v <= 1300 else 3 if v <= 1600 else 4
    )


def log_transition(ph_now, ec_now):
    if not tracking["wait_st1"]:
        return

    # Hitung State Baru dan Reward (Sesuai v6_final)
    s_idx = get_ph_idx(ph_now) * 5 + get_ec_idx(ec_now)
    reward = get_reward(s_idx)

    data = {
        "Sesi": f"AUTO_{VERSION_LOAD}",
        "Aksi": tracking["act"],
        "pH_St": tracking["st_ph"],
        "EC_St": tracking["st_ec"],
        "pH_St+1": ph_now,
        "EC_St+1": ec_now,
        "Delta_pH": round(ph_now - tracking["st_ph"], 2),
        "Delta_EC": round(ec_now - tracking["st_ec"], 2),
        "Reward": reward,
        "Max_Q": tracking["q"],
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    df = pd.DataFrame([data])
    df.to_csv(CSV_AUTO, mode="a", header=not os.path.exists(CSV_AUTO), index=False)
    print(
        f"[LOG] DATA DISIMPAN: {ACTIONS[tracking['act']]} | D_pH:{data['Delta_pH']} | D_EC:{data['Delta_EC']} | R:{reward}"
    )
    tracking["wait_st1"] = False


def push_action(action_id, is_retry=False):
    global waktu_resend_next, current_tx_id

    # Jika ini perintah baru (bukan retry), buat TXID baru
    if not is_retry:
        current_tx_id = str(int(time.time()))[-6:]  # 6 digit terakhir timestamp

    payload = f"{action_id}:{current_tx_id}"
    client.publish(TOPICS["action"], payload)
    write_log("SEND_ACTION", TOPICS["action"], payload)

    # Dynamic Timeout: Sesuaikan dengan durasi ESP32 Aktuator
    timeout_map = {7: 65, 8: 185}  # Air Baku S (60s), Air Baku L (180s)
    timeout = timeout_map.get(action_id, 15)

    waktu_resend_next = time.time() + timeout
    if not is_retry:
        print(f"[ACTION] Perintah Terkirim: {ACTIONS.get(action_id)} (ID:{payload})")
    return True


# ==========================================
# 2. HANDLER MQTT
# ==========================================
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT] Terhubung ke Broker! Model Aktif: {VERSION_LOAD}")
    for t in TOPICS.values():
        client.subscribe(t)


def on_message(client, userdata, msg):
    global status, waktu_homo_end, waktu_sampling_end
    payload = msg.payload.decode("utf-8")

    # A. Feedback Selesai dari ESP32 (Parsing JSON Latensi)
    if msg.topic == TOPICS["status"] and status == "DOSING":
        try:
            res = json.loads(payload)
            if res.get("tx") == current_tx_id and res.get("status") == "DONE":
                write_log("RECV_STATUS", msg.topic, payload)

                # Hitung Latensi (Jika ada timestamp)
                ts_esp = res.get("ts", 0)
                if ts_esp > 0:
                    now_ms = int(time.time() * 1000)
                    latensi = now_ms - ts_esp
                    print(
                        f"[STATUS] Selesai! ID: {res.get('tx')} | Latensi Sistem: {latensi}ms"
                    )
                else:
                    print(f"[STATUS] Selesai! ID: {res.get('tx')}")

                print(f"[HOMO] Memulai Masa Homogenisasi {WAKTU_HOMO} detik...")
                status, waktu_homo_end = "HOMO", time.time() + WAKTU_HOMO
        except Exception as e:
            # Backup untuk format lama jika perlu
            if payload == f"DONE:{current_tx_id}":
                status, waktu_homo_end = "HOMO", time.time() + WAKTU_HOMO
            else:
                print(f"[MQTT] Gagal parse status: {e}")

    # B. Monitoring Sensor & Keputusan AI
    elif msg.topic == TOPICS["sensor"]:
        write_log("RECV_SENSOR", msg.topic, payload)
        try:
            # 1. Parsing Data Sensor
            data = json.loads(payload)
            ph, ec = float(data.get("ph", 0)), float(data.get("ec", 0))

            # Monitoring Level Larutan (Remote Visual)
            v1, v2, v3, v4, v5 = (
                data.get("t1", 0),
                data.get("t2", 0),
                data.get("t3", 0),
                data.get("t4", 0),
                data.get("t5", 0),
            )
            vb = data.get("box", 0)

            print(
                f"\r[LEVELS] T1:{v1:.0f}ml | T2:{v2:.0f}ml | T3:{v3:.0f}ml | T4:{v4:.0f}ml | T5:{v5:.0f}ml | BOX:{vb:.1f}L ",
                end="",
                flush=True,
            )

            # Filter Safety Dasar
            if ph < 3 or ph > 9 or ec < 0 or ec > 3000:
                print(
                    f"\n[WARN] Data sensor tidak valid (pH:{ph}, EC:{ec}). Diabaikan."
                )
                return

            # --- SAFETY INTERLOCK TABUNG (T1-T5) ---
            tabung_levels = [v1, v2, v3, v4, v5]

            low_level = False
            if vb < 5.0:
                print(
                    f"\r[WAIT] Tandon Utama KRITIS ({vb:.1f}L)! Menunggu pengisian... ",
                    end="",
                    flush=True,
                )
                low_level = True

            for i, vol in enumerate(tabung_levels, 0):
                # Hanya cek safety jika saklarnya True
                if SAFETY_SWITCH[i] and vol < 100.0:
                    print(
                        f"\r[WAIT] Tabung T{i+1} KRITIS ({vol:.0f}ml)! Menunggu pengisian... ",
                        end="",
                        flush=True,
                    )
                    low_level = True

            # Logika Auto-Resume
            if low_level:
                status = "WAITING_REFILL"
                return
            elif status == "WAITING_REFILL":
                print("\n[RESUME] Air sudah terisi! Melanjutkan sistem...")
                status = "SAMPLING"
                waktu_sampling_end = time.time() + WAKTU_SAMPLING
                return

            if status == "HOMO":
                sisa = int(waktu_homo_end - time.time())
                if sisa <= 0:
                    print("[OK] Homogenisasi Selesai. Masuk masa Sampling (60s)...")
                    status, waktu_sampling_end = (
                        "SAMPLING",
                        time.time() + WAKTU_SAMPLING,
                    )
                    sampling_buffer["ph"], sampling_buffer["ec"] = [], []
                return

            if status == "SAMPLING":
                sampling_buffer["ph"].append(ph)
                sampling_buffer["ec"].append(ec)

                sisa = int(waktu_sampling_end - time.time())
                if sisa > 0:
                    if sisa % 15 == 0:
                        print(
                            f"[SAMPLING] Mengumpulkan data... ({len(sampling_buffer['ph'])} data, sisa {sisa}s)"
                        )
                    return

                # JIKA WAKTU SAMPLING HABIS, HITUNG RATA-RATA
                avg_ph = sum(sampling_buffer["ph"]) / len(sampling_buffer["ph"])
                avg_ec = sum(sampling_buffer["ec"]) / len(sampling_buffer["ec"])
                print(
                    f"[AVG] Hasil Rata-rata 1 Menit: pH:{avg_ph:.2f}, EC:{avg_ec:.0f}"
                )

                # RESET BUFFER INSTAN (Bug 3 Fix)
                sampling_buffer["ph"], sampling_buffer["ec"] = [], []

                # Record transisi dari siklus sebelumnya
                log_transition(avg_ph, avg_ec)

                # AMBIL KEPUTUSAN AI
                s_idx = get_ph_idx(avg_ph) * 5 + get_ec_idx(avg_ec)
                state_key = f"state_{s_idx + 1}"

                if state_key in policy_ai:
                    best_act = policy_ai[state_key]["best_action"]

                    if best_act == 0:  # IDLE
                        print(
                            f"[TARGET] Kondisi Optimal. Menunggu 1 menit untuk sampling berikutnya..."
                        )
                        tracking.update(
                            {
                                "wait_st1": True,
                                "st_ph": avg_ph,
                                "st_ec": avg_ec,
                                "act": 0,
                                "q": policy_ai[state_key]["max_q"],
                            }
                        )
                        status, waktu_sampling_end = (
                            "SAMPLING",
                            time.time() + WAKTU_SAMPLING,
                        )
                        return

                    if MAX_ACTIONS > 0 and tracking["total_actions"] >= MAX_ACTIONS:
                        print(f"\n[FINISH] Uji Keandalan {MAX_ACTIONS} Aksi Selesai.")
                        status = "FINISH"
                        return

                    tracking["total_actions"] += 1

                    print(
                        f"\n[AI] Aksi ke-{tracking['total_actions']}/{MAX_ACTIONS if MAX_ACTIONS > 0 else 'INF'} | State: {state_key} | Action: {ACTIONS[best_act]}"
                    )

                    tracking.update(
                        {
                            "wait_st1": True,
                            "st_ph": avg_ph,
                            "st_ec": avg_ec,
                            "act": best_act,
                            "q": policy_ai[state_key]["max_q"],
                        }
                    )

                    waktu_resend_next = 0
                    if push_action(best_act):
                        status = "DOSING"

        except Exception as e:
            # Bug 2 Fix: Jangan telan error diam-diam
            print(f"[ERROR] on_message exception: {e}")


# ==========================================
# 3. MAIN RUN LOOP
# ==========================================
if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("    SISTEM KONTROL OTOMATIS: HYDRO-AI B600 v4    ")
    print("=" * 55)

    if not os.path.exists(POLICY_FILE):
        print(f"[ERROR] File {POLICY_FILE} tidak ditemukan!")
        exit()

    with open(POLICY_FILE, "r") as f:
        policy_ai = json.load(f)
    print(f"[DATA] Memuat {len(policy_ai)} skenario kecerdasan AI.")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect, client.on_message = on_connect, on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        while True:
            # RETRY LOGIC: Jika sedang DOSING tapi tidak ada kabar 'DONE' dari ESP32
            if status == "DOSING" and time.time() > waktu_resend_next:
                print(
                    f"[RETRY] ESP32 tidak merespon. Mengirim ulang ID:{current_tx_id}..."
                )
                write_log("RETRY_ACTION", TOPICS["action"], f"resend {current_tx_id}")
                push_action(tracking["act"], is_retry=True)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[STOP] Sistem dimatikan secara manual.")
        client.loop_stop()
        client.disconnect()
