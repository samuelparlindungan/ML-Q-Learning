import paho.mqtt.client as mqtt
import time, json, os, pandas as pd
import csv, threading
from datetime import datetime
from env_ph_ec import PhEcEnv

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
VERSION_LOAD = "v6_final"
CSV_AUTO = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "output", "data_transisi_otomatis.csv")
)
POLICY_FILE = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "output", VERSION_LOAD, "policy.json")
)
LOG_FILE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "output", "system_log.csv"))

MAX_STEPS = 50  # <-- Diganti dari MAX_ACTIONS
WAKTU_HOMO = 180
WAKTU_SAMPLING = 60

# --- Shared State (dilindungi RLock) ---
lock = threading.RLock()

status = "SAMPLING"
waktu_homo_end = 0
waktu_sampling_end = time.time() + WAKTU_SAMPLING
waktu_resend_next = 0
waktu_kirim = 0
current_tx_id = ""
policy_ai = {}
sampling_buffer = {"ph": [], "ec": []}
tracking = {
    "wait_st1": False,
    "st_ph": 0.0,
    "st_ec": 0.0,
    "act": -1,
    "q": 0.0,
    "total_steps": 0,  # <-- Diganti dari total_actions
}

SAFETY_SWITCH = [True, True, True, True, True]

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

MAX_RETRIES = 3
retry_count = 0

# Throttle [LEVELS]
_last_level_print = 0
LEVEL_PRINT_INTERVAL = 5
_level_printed = False  # Cetak level hanya sekali di awal


# ==========================================
# 1. FUNGSI PEMBANTU
# ==========================================
def get_ph_idx(v):
    """Konversi pH ke indeks 0-4 sesuai Tabel 3.1"""
    if v < 5.5:
        return 0
    elif v < 5.8:
        return 1
    elif v <= 6.2:
        return 2
    elif v <= 6.5:
        return 3
    else:
        return 4


def get_ec_idx(v):
    """Konversi EC ke indeks 0-4 sesuai Tabel 3.2"""
    if v < 800:
        return 0
    elif v < 1100:
        return 1
    elif v <= 1300:
        return 2
    elif v <= 1600:
        return 3
    else:
        return 4


def get_reward(ph, ec):
    """Hitung reward berdasarkan Tabel 3.6 Bab 3"""
    env = PhEcEnv()
    state = get_ph_idx(ph) * 5 + get_ec_idx(ec)
    return env.reward_table[state]


def write_log(event_type, topic, detail=""):
    file_exists = os.path.isfile(LOG_FILE)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "event_type", "topic", "detail"])
        writer.writerow([datetime.now().isoformat(), event_type, topic, detail])


def log_transition(ph_now, ec_now):
    with lock:
        if not tracking["wait_st1"]:
            return
        reward = get_reward(ph_now, ec_now)
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
        tracking["wait_st1"] = False
    df = pd.DataFrame([data])
    df.to_csv(CSV_AUTO, mode="a", header=not os.path.exists(CSV_AUTO), index=False)
    print(
        f"[LOG] DATA DISIMPAN: {ACTIONS[data['Aksi']]} | D_pH:{data['Delta_pH']} | D_EC:{data['Delta_EC']} | R:{data['Reward']}"
    )


def push_action(action_id, is_retry=False):
    """Harus dipanggil di dalam 'with lock'."""
    global waktu_resend_next, current_tx_id, waktu_kirim, retry_count

    if not is_retry:
        current_tx_id = str(int(time.time()))[-6:]
        waktu_kirim = time.time()
        retry_count = 0

    payload = f"{action_id}:{current_tx_id}"
    client.publish(TOPICS["action"], payload)
    write_log("SEND_ACTION", TOPICS["action"], payload)

    timeout_map = {7: 65, 8: 185}
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
    global status, waktu_homo_end, waktu_sampling_end, retry_count, _last_level_print, _level_printed
    payload = msg.payload.decode("utf-8")

    # --- Guard HALT & Snapshot status (dengan lock) ---
    with lock:
        if status == "HALT":
            return
        current_status = status  # snapshot untuk konsistensi di cabang pertama

    # A. Feedback Selesai dari ESP32
    if msg.topic == TOPICS["status"] and current_status == "DOSING":
        try:
            res = json.loads(payload)
            if res.get("tx") == current_tx_id and res.get("status") == "DONE":
                write_log("RECV_STATUS", msg.topic, payload)
                latensi = int((time.time() - waktu_kirim) * 1000)
                print(f"[STATUS] Selesai! ID: {res.get('tx')} | Latensi: {latensi}ms")
                with lock:
                    status = "HOMO"
                    waktu_homo_end = time.time() + WAKTU_HOMO
                    retry_count = 0
        except Exception:
            if payload == f"DONE:{current_tx_id}":
                with lock:
                    status = "HOMO"
                    waktu_homo_end = time.time() + WAKTU_HOMO
                    retry_count = 0
            else:
                print(f"[MQTT] Gagal parse status: {payload[:50]}")
        return  # Selesai proses status feedback

    # B. Monitoring Sensor & Keputusan AI
    if msg.topic != TOPICS["sensor"]:
        return

    write_log("RECV_SENSOR", msg.topic, payload)
    try:
        data = json.loads(payload)
        ph, ec = float(data.get("ph", 0)), float(data.get("ec", 0))

        v1, v2, v3, v4, v5 = (
            data.get("t1", 0),
            data.get("t2", 0),
            data.get("t3", 0),
            data.get("t4", 0),
            data.get("t5", 0),
        )
        vb = data.get("box", 0)

        if ph < 3 or ph > 9 or ec < 0 or ec > 3000:
            return

        tabung_levels = [v1, v2, v3, v4, v5]

        # Safety interlock
        low_level = False
        if vb < 5.0:
            print(f"[WAIT] Tandon Utama KRITIS ({vb:.1f}L)! Menunggu pengisian...")
            low_level = True
        for i, vol in enumerate(tabung_levels):
            if SAFETY_SWITCH[i] and vol < 100.0:
                print(
                    f"[WAIT] Tabung T{i+1} KRITIS ({vol:.0f}ml)! Menunggu pengisian..."
                )
                low_level = True

        # Cetak level hanya sekali di awal
        with lock:
            if not _level_printed:
                level_str = " | ".join(
                    [
                        f"T{i+1}:{v:.0f}ml" if SAFETY_SWITCH[i] else f"T{i+1}:OFF"
                        for i, v in enumerate(tabung_levels)
                    ]
                )
                print(f"[LEVELS] {level_str} | Box:{vb:.1f}L")
                _level_printed = True

        # --- State Management dengan re-snapshot setiap langkah ---

        # 1. Cek low level & transisi WAITING_REFILL
        if low_level:
            with lock:
                status = "WAITING_REFILL"
            return

        # 2. Jika tadi WAITING_REFILL, sekarang low_level sudah False -> resume langsung ke SAMPLING
        with lock:
            if status == "WAITING_REFILL":
                print("[RESUME] Air sudah terisi! Melanjutkan sistem...")
                status = "SAMPLING"
                waktu_sampling_end = time.time() + WAKTU_SAMPLING
                sampling_buffer["ph"], sampling_buffer["ec"] = [], []
                retry_count = 0
            # Ambil snapshot ulang karena status bisa berubah
            current_status = status

        # 3. State HOMO
        if current_status == "HOMO":
            with lock:
                if waktu_homo_end <= time.time():
                    status = "SAMPLING"
                    waktu_sampling_end = time.time() + WAKTU_SAMPLING
                    sampling_buffer["ph"], sampling_buffer["ec"] = [], []
                    retry_count = 0
                    current_status = status
                else:
                    current_status = "HOMO"
            if current_status != "SAMPLING":
                return
            return

        # 4. State SAMPLING
        if current_status == "SAMPLING":
            with lock:
                sampling_buffer["ph"].append(ph)
                sampling_buffer["ec"].append(ec)
                sisa = waktu_sampling_end - time.time()
            if sisa > 0:
                return

            # Guard buffer kosong
            if not sampling_buffer["ph"]:
                print("[WARN] Buffer sampling kosong, skip siklus ini.")
                with lock:
                    waktu_sampling_end = time.time() + WAKTU_SAMPLING
                return

            # Hitung rata-rata
            with lock:
                avg_ph = sum(sampling_buffer["ph"]) / len(sampling_buffer["ph"])
                avg_ec = sum(sampling_buffer["ec"]) / len(sampling_buffer["ec"])
                sampling_buffer["ph"], sampling_buffer["ec"] = [], []

            print(f"[SENSOR] Hasil Pembacaan: pH:{avg_ph:.2f}, EC:{avg_ec:.0f}")

            # Log transisi sebelumnya
            log_transition(avg_ph, avg_ec)

            # Keputusan AI
            s_idx = get_ph_idx(avg_ph) * 5 + get_ec_idx(avg_ec)
            state_key = f"state_{s_idx + 1}"

            if state_key not in policy_ai:
                print(f"[WARN] State {state_key} tidak ditemukan di policy!")
                with lock:
                    waktu_sampling_end = time.time() + WAKTU_SAMPLING
                return

            best_act = policy_ai[state_key]["best_action"]
            p_idx, e_idx = get_ph_idx(avg_ph), get_ec_idx(avg_ec)
            ph_labels = ["S.Rendah", "Rendah", "Optimal", "Tinggi", "S.Tinggi"]
            ec_labels = ["S.Rendah", "Rendah", "Optimal", "Tinggi", "S.Tinggi"]

            # Batas langkah (STEP)
            with lock:
                total_steps = tracking["total_steps"]
            if MAX_STEPS > 0 and total_steps >= MAX_STEPS:
                print(f"[FINISH] Uji Keandalan {MAX_STEPS} Step Selesai.")
                with lock:
                    status = "FINISH"
                return

            # --- Increment step (SETIAP SIKLUS) ---
            with lock:
                tracking["total_steps"] += 1
                total_steps = tracking["total_steps"]
                tracking.update(
                    {
                        "wait_st1": True,
                        "st_ph": avg_ph,
                        "st_ec": avg_ec,
                        "act": best_act,
                        "q": policy_ai[state_key]["max_q"],
                    }
                )

            if best_act == 0:  # IDLE
                print(
                    f"[STEP {total_steps}/{MAX_STEPS}] IDLE | State: {state_key} (pH:{ph_labels[p_idx]}, EC:{ec_labels[e_idx]}) | Kondisi Optimal."
                )
                with lock:
                    waktu_sampling_end = time.time() + WAKTU_SAMPLING
                    retry_count = 0
                return

            # NON-IDLE
            print(
                f"[STEP {total_steps}/{MAX_STEPS}] {ACTIONS[best_act]} | State: {state_key} (pH:{ph_labels[p_idx]}, EC:{ec_labels[e_idx]})"
            )
            with lock:
                if push_action(best_act):
                    status = "DOSING"
            return

    except Exception as e:
        print(f"[ERROR] on_message exception: {e}")


# ==========================================
# 3. MAIN RUN LOOP
# ==========================================
if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("    SISTEM KONTROL OTOMATIS: RL Q-Learning    ")
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
            with lock:
                if status == "DOSING" and time.time() > waktu_resend_next:
                    if retry_count < MAX_RETRIES:
                        print(
                            f"[RETRY] ESP32 tidak merespon. Mengirim ulang ID:{current_tx_id} "
                            f"(percobaan ke-{retry_count+1}/{MAX_RETRIES})..."
                        )
                        write_log(
                            "RETRY_ACTION", TOPICS["action"], f"resend {current_tx_id}"
                        )
                        push_action(tracking["act"], is_retry=True)
                        retry_count += 1
                    else:
                        print(
                            "[ERROR] ESP32 tidak merespon setelah 3 kali percobaan. Sistem HALT sementara."
                        )
                        status = "HALT"
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[STOP] Sistem dimatikan secara manual.")
        client.loop_stop()
        client.disconnect()
