import paho.mqtt.client as mqtt
import time, json, os, pandas as pd
import csv
from datetime import datetime

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
WAKTU_HOMO = 180  # 3 Menit
WAKTU_SAMPLING = 60  # 1 Menit Averaging Window

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
}

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
    data = {
        "Sesi": f"AUTO_{VERSION_LOAD}",
        "Aksi": tracking["act"],
        "pH_St": tracking["st_ph"],
        "EC_St": tracking["st_ec"],
        "pH_St+1": ph_now,
        "EC_St+1": ec_now,
        "Delta_pH": round(ph_now - tracking["st_ph"], 2),
        "Delta_EC": round(ec_now - tracking["st_ec"], 2),
        "Max_Q": tracking["q"],
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    df = pd.DataFrame([data])
    df.to_csv(CSV_AUTO, mode="a", header=not os.path.exists(CSV_AUTO), index=False)
    print(
        f"📝 [LOG] DATA DISIMPAN: {ACTIONS[tracking['act']]} | D_pH:{data['Delta_pH']} | D_EC:{data['Delta_EC']}"
    )
    tracking["wait_st1"] = False


def push_action(action_id):
    global waktu_resend_next, current_tx_id

    # Jika ini perintah baru (bukan retry), buat TXID baru
    if time.time() > waktu_resend_next:
        current_tx_id = str(int(time.time()))[-6:]  # 6 digit terakhir timestamp

    payload = f"{action_id}:{current_tx_id}"
    client.publish(TOPICS["action"], payload)
    write_log("SEND_ACTION", TOPICS["action"], payload)

    waktu_resend_next = time.time() + 15  # Set timeout 15 detik untuk retry
    print(f"🚀 [ACTION] Perintah Terkirim: {ACTIONS.get(action_id)} (ID:{payload})")
    return True


# ==========================================
# 2. HANDLER MQTT
# ==========================================
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"✅ [MQTT] Terhubung ke Broker! Model Aktif: {VERSION_LOAD}")
    for t in TOPICS.values():
        client.subscribe(t)


def on_message(client, userdata, msg):
    global status, waktu_homo_end
    payload = msg.payload.decode("utf-8")

    # A. Feedback Selesai dari ESP32 (Harus Cocok ID-nya)
    if msg.topic == TOPICS["status"] and status == "DOSING":
        if payload == f"DONE:{current_tx_id}":
            write_log("RECV_STATUS", msg.topic, payload)
            print(f"📥 [STATUS] ESP32 mengonfirmasi: {payload} SELESAI.")
            print(f"⏳ [HOMO] Memulai Masa Homogenisasi {WAKTU_HOMO} detik...")
            status, waktu_homo_end = "HOMO", time.time() + WAKTU_HOMO
        elif payload.startswith("DONE:"):
            print(f"⚠️ [IGNORE] Menerima konfirmasi ID lama: {payload}")

    # B. Monitoring Sensor & Keputusan AI
    elif msg.topic == TOPICS["sensor"]:
        write_log("RECV_SENSOR", msg.topic, payload)
        try:
            data = json.loads(payload)
            ph, ec = float(data.get("ph", 0)), float(data.get("ec", 0))

            # Filter Safety Dasar
            if ph < 3 or ph > 9 or ec < 100 or ec > 3000:
                return

            if status == "HOMO":
                sisa = int(waktu_homo_end - time.time())
                if sisa <= 0:
                    print("✨ [OK] Homogenisasi Selesai. Masuk masa Sampling (60s)...")
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
                            f"📊 [SAMPLING] Mengumpulkan data... ({len(sampling_buffer['ph'])} data, sisa {sisa}s)"
                        )
                    return

                # JIKA WAKTU SAMPLING HABIS, HITUNG RATA-RATA
                avg_ph = sum(sampling_buffer["ph"]) / len(sampling_buffer["ph"])
                avg_ec = sum(sampling_buffer["ec"]) / len(sampling_buffer["ec"])
                print(
                    f"📈 [AVG] Hasil Rata-rata 1 Menit: pH:{avg_ph:.2f}, EC:{avg_ec:.0f}"
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
                        print(f"🎯 [TARGET] Kondisi Optimal. Menunggu 1 menit untuk sampling berikutnya...")
                        tracking.update({
                            "wait_st1": True,
                            "st_ph": avg_ph,
                            "st_ec": avg_ec,
                            "act": 0,
                            "q": policy_ai[state_key]["max_q"],
                        })
                        status, waktu_sampling_end = "SAMPLING", time.time() + WAKTU_SAMPLING
                        return

                    print(f"\n🧠 [AI] State: {state_key} | Action: {ACTIONS[best_act]}")
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
            print(f"⚠️ [ERROR] on_message exception: {e}")


# ==========================================
# 3. MAIN RUN LOOP
# ==========================================
if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("🤖   SISTEM KONTROL OTOMATIS: HYDRO-AI B600 v4   🤖")
    print("=" * 55)

    if not os.path.exists(POLICY_FILE):
        print(f"❌ [ERROR] File {POLICY_FILE} tidak ditemukan!")
        exit()

    with open(POLICY_FILE, "r") as f:
        policy_ai = json.load(f)
    print(f"📚 [DATA] Memuat {len(policy_ai)} skenario kecerdasan AI.")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect, client.on_message = on_connect, on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        while True:
            # RETRY LOGIC: Jika sedang DOSING tapi tidak ada kabar 'DONE' dari ESP32
            if status == "DOSING" and time.time() > waktu_resend_next:
                print(
                    f"⚠️ [RETRY] ESP32 tidak merespon. Mengirim ulang ID:{current_tx_id}..."
                )
                write_log("RETRY_ACTION", TOPICS["action"], f"resend {current_tx_id}")
                push_action(tracking["act"])

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 [STOP] Sistem dimatikan secara manual.")
        client.loop_stop()
        client.disconnect()
