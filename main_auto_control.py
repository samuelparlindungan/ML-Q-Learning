import paho.mqtt.client as mqtt
import time, json, os, pandas as pd
from datetime import datetime

# ==========================================
# 0. KONFIGURASI SISTEM
# ==========================================
MQTT_BROKER, MQTT_PORT = "192.168.100.10", 1883
TOPICS = {"sensor": "hidroponik/sensor", "action": "hidroponik/action", "status": "hidroponik/status"}
CSV_AUTO = "output/data_transisi_otomatis.csv"
POLICY_FILE = "output/policy.json"
WAKTU_HOMO = 180 # 3 Menit

# State Tracking
status, waktu_homo_end = "STANDBY", 0
policy_ai, tracking = {}, {"wait_st1": False, "st_ph": 0.0, "st_ec": 0.0, "act": -1, "q": 0.0}

# Mapping Aksi (Tabel 3.4 B600)
ACTIONS = {
    0: "IDLE", 1: "pH Up S", 2: "pH Up L", 3: "pH Down S", 
    4: "pH Down L", 5: "Nutrisi S", 6: "Nutrisi L", 7: "Air S", 8: "Air L"
}

# ==========================================
# 1. FUNGSI PEMBANTU (UTILITIES)
# ==========================================
def get_ph_idx(v): return 0 if v<5.5 else 1 if v<5.8 else 2 if v<=6.2 else 3 if v<=6.5 else 4
def get_ec_idx(v): return 0 if v<800 else 1 if v<1100 else 2 if v<=1300 else 3 if v<=1600 else 4

def log_transition(ph_now, ec_now):
    if not tracking["wait_st1"]: return
    data = {
        "Sesi": "AUTO_DEPLOY", "Aksi": tracking["act"], 
        "pH_St": tracking["st_ph"], "EC_St": tracking["st_ec"],
        "pH_St+1": ph_now, "EC_St+1": ec_now,
        "Delta_pH": round(ph_now - tracking["st_ph"], 2),
        "Delta_EC": round(ec_now - tracking["st_ec"], 2),
        "Max_Q": tracking["q"], "Time": datetime.now().strftime("%H:%M:%S")
    }
    df = pd.DataFrame([data])
    df.to_csv(CSV_AUTO, mode='a', header=not os.path.exists(CSV_AUTO), index=False)
    print(f"[LOG] Transisi Tercatat: {ACTIONS[tracking['act']]} -> pH:{ph_now} EC:{ec_now}")
    tracking["wait_st1"] = False

def push_action(action_id):
    client.publish(TOPICS["action"], str(action_id))
    print(f"[ACTION] Eksekusi: {ACTIONS.get(action_id, 'UNK')} (ID:{action_id})")
    return True

# ==========================================
# 2. HANDLER MQTT (CORE LOGIC)
# ==========================================
def on_connect(client, userdata, flags, reason_code, properties):
    print("[MQTT] Terhubung! Menunggu data sensor...")
    for t in TOPICS.values(): client.subscribe(t)

def on_message(client, userdata, msg):
    global status, waktu_homo_end
    payload = msg.payload.decode("utf-8")

    # A. Feedback Selesai dari ESP32
    if msg.topic == TOPICS["status"] and payload == "DONE" and status == "DOSING":
        print("[INFO] Dosing selesai. Mulai Homogenisasi 3 Menit...")
        status, waktu_homo_end = "HOMO", time.time() + WAKTU_HOMO

    # B. Input Sensor & Keputusan AI
    elif msg.topic == TOPICS["sensor"]:
        if status == "HOMO":
            if time.time() >= waktu_homo_end:
                print("[OK] Homogenisasi selesai. Sistem kembali STANDBY."); status = "STANDBY"
            return

        if status == "STANDBY":
            try:
                data = json.loads(payload)
                ph, ec = float(data.get("ph", 0)), float(data.get("ec", 0))

                # --- SAFETY INTERLOCK ---
                if ph < 0 or ph > 14 or ec < 0 or ec > 5000:
                    print(f"[BAHAYA] Anomali: pH:{ph} EC:{ec}. Aksi DIBLOKIR!"); return

                # Log St+1 jika ini observasi pertama setelah aksi sebelumnya
                log_transition(ph, ec)

                # Ambil Keputusan AI
                s_idx = get_ph_idx(ph) * 5 + get_ec_idx(ec)
                state_key = f"state_{s_idx + 1}"
                
                if state_key in policy_ai:
                    best_act = policy_ai[state_key]["best_action"]
                    print(f"[DATA] pH:{ph:.2f} EC:{ec:.2f} | Local State: {state_key}")
                    
                    # Update tracking untuk log masa depan
                    tracking.update({"wait_st1": True, "st_ph": ph, "st_ec": ec, "act": best_act, "q": policy_ai[state_key]["max_q"]})
                    
                    if push_action(best_act): status = "DOSING"

            except Exception as e: print(f"[ERROR] Logic Error: {e}")

# ==========================================
# 3. MAIN
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*45 + "\n[SYSTEM] KENDALI HIDROPONIK AI (B600 ON-POINT)\n" + "="*45)
    
    os.makedirs("output", exist_ok=True)
    if not os.path.exists(POLICY_FILE):
        print("[ERROR] Policy.json tidak ditemukan!"); exit()
        
    with open(POLICY_FILE, "r") as f: policy_ai = json.load(f)
    print(f"[OK] {len(policy_ai)} Intelligence patterns loaded.")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect, client.on_message = on_connect, on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[STOP] Offline."); client.disconnect()
