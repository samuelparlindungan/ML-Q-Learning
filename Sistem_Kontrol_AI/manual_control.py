import paho.mqtt.client as mqtt
import sys
import time

# KONFIGURASI
MQTT_BROKER = "192.168.100.10"
TOPIC_MAINTEN = "hidroponik/maintenance"


def main():
    if len(sys.argv) < 3:
        print("\n🤖 HYDRO-AI MANUAL CONTROL 🤖")
        print("Penggunaan: python manual_control.py [ID_POMPA] [DETIK]")
        print("ID Pompa: 1-5 (atau 0 untuk STOP SEMUA)")
        print("Contoh: python manual_control.py 5 2 (Pompa 5 selama 2 detik)\n")
        return

    pump_id = sys.argv[1]
    duration = sys.argv[2]
    payload = f"{pump_id} {duration}"

    client = mqtt.Client()
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        client.publish(TOPIC_MAINTEN, payload)
        print(f"🚀 [SENT] Mengirim ke ESP32 -> Pompa:{pump_id} Durasi:{duration} detik")
        time.sleep(0.5)  # Beri waktu untuk publish
        client.disconnect()
        print("✅ Selesai.")
    except Exception as e:
        print(f"❌ [ERROR] Gagal terhubung ke broker: {e}")


if __name__ == "__main__":
    main()
