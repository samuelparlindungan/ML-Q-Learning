#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==========================================
// 1. KONFIGURASI WIFI & MQTT BROKER
// ==========================================
const char* ssid        = "XinXun-9988";         
const char* password    = "12345678";            
const char* mqtt_server = "192.168.100.10";  

WiFiClient espClient;
PubSubClient client(espClient);

// Topik Komunikasi MQTT
const char* topic_sensor = "hidroponik/sensor"; 
const char* topic_action = "hidroponik/action"; 
const char* topic_status = "hidroponik/status"; 

// ==========================================
// 2. PIN RELAY (Active Low)
// ==========================================
const int RELAY_PH_UP   = 26; 
const int RELAY_PH_DOWN = 27; 
const int RELAY_NUT_A   = 25; 
const int RELAY_NUT_B   = 32; 
const int RELAY_AIR     = 33; 

// ==========================================
// 3. VARIABEL DURASI & SAFETY INTERLOCK
// ==========================================
const unsigned long T_SHORT = 2000; // 2 Detik
const unsigned long T_LONG  = 5000; // 5 Detik

// Kapasitas Box Maksimal = 21.85L.
float volume_tandon_saat_ini = 21.85; 
const float BATAS_KRITIS_AIR = 5.0; // Jika di bawah 5L, pompa diblokir

// ==========================================
// FUNGSI KONTROL POMPA
// ==========================================
void jalankanPompa(int pin_pompa, unsigned long durasi) {
  digitalWrite(pin_pompa, LOW); 
  delay(durasi); 
  digitalWrite(pin_pompa, HIGH);
}

void jalankanNutrisi(unsigned long durasi) {
  digitalWrite(RELAY_NUT_A, LOW); 
  digitalWrite(RELAY_NUT_B, LOW);
  delay(durasi);
  digitalWrite(RELAY_NUT_A, HIGH); 
  digitalWrite(RELAY_NUT_B, HIGH);
}

// ==========================================
// SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  
  pinMode(RELAY_PH_UP, OUTPUT); 
  pinMode(RELAY_PH_DOWN, OUTPUT);
  pinMode(RELAY_NUT_A, OUTPUT); 
  pinMode(RELAY_NUT_B, OUTPUT);
  pinMode(RELAY_AIR, OUTPUT);

  // Matikan semua relay di awal (Active Low = HIGH)
  digitalWrite(RELAY_PH_UP, HIGH); 
  digitalWrite(RELAY_PH_DOWN, HIGH);
  digitalWrite(RELAY_NUT_A, HIGH); 
  digitalWrite(RELAY_NUT_B, HIGH);
  digitalWrite(RELAY_AIR, HIGH);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print("."); 
  }
  Serial.println("\n[WiFi] Aktuator Terhubung!");

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("[MQTT] Menghubungkan Aktuator...");
    if (client.connect("ESP32_Aktuator_Unit2")) {
      Serial.println(" OK!");
      // ESP32 Aktuator berlangganan ke 2 topik
      client.subscribe(topic_action); // Perintah AI/Python
      client.subscribe(topic_sensor); // Cek JSON teman (untuk Box)
    } else {
      delay(5000);
    }
  }
}

// ==========================================
// FUNGSI CALLBACK (PENERIMA PESAN MQTT)
// ==========================================
void callback(char* topic, byte* payload, unsigned int length) {
  String pesan = "";
  for (int i = 0; i < length; i++) pesan += (char)payload[i];

  // --- LOGIKA 1: UPDATE DATA SENSOR (SAFETY INTERLOCK) ---
  if (String(topic) == String(topic_sensor)) {
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, pesan);
    if (!error) {
      // Ambil kunci "box" dari JSON teman Anda
      volume_tandon_saat_ini = doc["box"];
    }
    return; // Selesai membaca sensor, tidak perlu lanjut ke bawah
  }

  // --- LOGIKA 2: EKSEKUSI PERINTAH AKSI ---
  if (String(topic) == String(topic_action)) {
    int aksi = pesan.toInt();
    Serial.print("\n[PERINTAH MASUK] Aksi: "); 
    Serial.println(aksi);

    // Cek Safety Interlock: Apakah air di tandon cukup?
    if (volume_tandon_saat_ini < BATAS_KRITIS_AIR && aksi != 0) {
      Serial.println("⚠️ BAHAYA: Tandon Utama Kosong/Kritis!");
      Serial.println("⛔ Perintah Pompa DIBLOKIR oleh Safety Interlock.");
    } else {
      // Eksekusi Pompa (Tabel 3.4 B600)
      switch(aksi) {
        case 0: Serial.println("Eksekusi: Idle"); break;
        case 1: Serial.println("Eksekusi: pH Up Short"); jalankanPompa(RELAY_PH_UP, T_SHORT); break;
        case 2: Serial.println("Eksekusi: pH Up Long"); jalankanPompa(RELAY_PH_UP, T_LONG); break;
        case 3: Serial.println("Eksekusi: pH Down Short"); jalankanPompa(RELAY_PH_DOWN, T_SHORT); break;
        case 4: Serial.println("Eksekusi: pH Down Long"); jalankanPompa(RELAY_PH_DOWN, T_LONG); break;
        case 5: Serial.println("Eksekusi: Nutrisi Short"); jalankanNutrisi(T_SHORT); break;
        case 6: Serial.println("Eksekusi: Nutrisi Long"); jalankanNutrisi(T_LONG); break;
        case 7: Serial.println("Eksekusi: Air Baku Short"); jalankanPompa(RELAY_AIR, T_SHORT); break;
        case 8: Serial.println("Eksekusi: Air Baku Long"); jalankanPompa(RELAY_AIR, T_LONG); break;
        default: Serial.println("Aksi tidak dikenal!"); break;
      }
    }

    // --- LOGIKA 3: PUBLISH STATUS SELESAI (DONE) ---
    // Memberi tahu Python bahwa proses hardware sudah selesai/terblokir
    Serial.println("Selesai. Mengirim sinyal DONE ke Python...");
    client.publish(topic_status, "DONE");
  }
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
}