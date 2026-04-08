#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// 1. KONFIGURASI WIFI & MQTT
// ==========================================
const char* ssid        = "XinXun-9988";
const char* password    = "12345678";
const char* mqtt_server = "192.168.100.10";
const int   mqtt_port   = 1883;

// Topik Komunikasi (Wajib sama dengan Python)
const char* topic_action = "hidroponik/action"; 
const char* topic_status = "hidroponik/status"; 

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ==========================================
// 2. DEFINISI PIN RELAY (Sesuai Hardware Anda)
// ==========================================
// Relay 1 (4-Channel)
const int RELAY_PH_UP   = 14; 
const int RELAY_PH_DN   = 27; 
const int RELAY_AIR     = 26; 
const int RELAY_NUT_A   = 25; 

// Relay 2 (2-Channel, pakai 1)
const int RELAY_NUT_B   = 33; 

// ==========================================
// 3. DURASI POMPA (Hasil Rekomendasi Anda)
// ==========================================
const unsigned long t_ph_short  = 2000;   // pH 2 detik
const unsigned long t_ph_long   = 5000;   // pH 5 detik
const unsigned long t_nut_short = 2000;   // Nutrisi 2 detik
const unsigned long t_nut_long  = 6000;   // Nutrisi 6 detik
const unsigned long t_air_short = 5000;   // Air Baku 5 detik
const unsigned long t_air_long  = 15000;  // Air Baku 15 detik

// Variabel eksekusi
int current_action = -1;
bool action_pending = false;

// ==========================================
// FUNGSI SMART DELAY (Mencegah MQTT Putus)
// ==========================================
// Fungsi ini menggantikan delay() biasa agar saat pompa menyala 15 detik,
// ESP32 tetap menjaga koneksi ke Broker MQTT tidak terputus.
void smartDelay(unsigned long ms) {
  unsigned long start = millis();
  while (millis() - start < ms) {
    mqttClient.loop(); // Jaga detak jantung MQTT
    delay(10);
  }
}

// ==========================================
// FUNGSI KONEKSI WIFI & MQTT
// ==========================================
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Konek ke WiFi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi OK!");
}

void reconnect() {
  while (!mqttClient.connected()) {
    Serial.print("Konek ke MQTT...");
    // Buat Client ID unik
    String clientId = "ESP32_Aktuator_";
    clientId += String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("OK!");
      // Subscribe ke topik aksi
      mqttClient.subscribe(topic_action); 
    } else {
      Serial.print("Gagal, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Coba lagi dalam 5 dtk");
      delay(5000);
    }
  }
}

// ==========================================
// FUNGSI CALLBACK (Menangkap Perintah Python)
// ==========================================
void callback(char* topic, byte* payload, unsigned int length) {
  String messageTemp;
  for (int i = 0; i < length; i++) {
    messageTemp += (char)payload[i];
  }
  
  Serial.print("Perintah Masuk: Aksi ");
  Serial.println(messageTemp);

  current_action = messageTemp.toInt();
  action_pending = true; 
}

// ==========================================
// SETUP AWAL
// ==========================================
void setup() {
  Serial.begin(115200);

  // 1. Atur PIN sebagai OUTPUT
  pinMode(RELAY_PH_UP, OUTPUT); 
  pinMode(RELAY_PH_DN, OUTPUT); 
  pinMode(RELAY_NUT_A, OUTPUT); 
  pinMode(RELAY_NUT_B, OUTPUT); 
  pinMode(RELAY_AIR,   OUTPUT); 

  // 2. Matikan Semua Relay di Awal (Active LOW = HIGH untuk Mati)
  digitalWrite(RELAY_PH_UP, HIGH);
  digitalWrite(RELAY_PH_DN, HIGH);
  digitalWrite(RELAY_NUT_A, HIGH);
  digitalWrite(RELAY_NUT_B, HIGH);
  digitalWrite(RELAY_AIR,   HIGH);

  // 3. Mulai Koneksi
  setup_wifi();
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);
}

// ==========================================
// FUNGSI EKSEKUSI POMPA (Sesuai 9 Aksi Q-Learning)
// ==========================================
void eksekusiPompa(int aksi) {
  Serial.print("Mengeksekusi Aksi: ");
  Serial.println(aksi);

  switch(aksi) {
    case 0: // Idle
      Serial.println("Idle - Tidak ada pompa menyala.");
      smartDelay(1000); // Jeda basa-basi 1 detik
      break;
    
    case 1: // pH Up Short
      digitalWrite(RELAY_PH_UP, LOW); smartDelay(t_ph_short); digitalWrite(RELAY_PH_UP, HIGH);
      break;
    case 2: // pH Up Long
      digitalWrite(RELAY_PH_UP, LOW); smartDelay(t_ph_long);  digitalWrite(RELAY_PH_UP, HIGH);
      break;

    case 3: // pH Down Short
      digitalWrite(RELAY_PH_DN, LOW); smartDelay(t_ph_short); digitalWrite(RELAY_PH_DN, HIGH);
      break;
    case 4: // pH Down Long
      digitalWrite(RELAY_PH_DN, LOW); smartDelay(t_ph_long);  digitalWrite(RELAY_PH_DN, HIGH);
      break;

    case 5: // Nutrisi Short (A & B bersamaan)
      digitalWrite(RELAY_NUT_A, LOW); digitalWrite(RELAY_NUT_B, LOW); 
      smartDelay(t_nut_short); 
      digitalWrite(RELAY_NUT_A, HIGH); digitalWrite(RELAY_NUT_B, HIGH);
      break;
    case 6: // Nutrisi Long (A & B bersamaan)
      digitalWrite(RELAY_NUT_A, LOW); digitalWrite(RELAY_NUT_B, LOW); 
      smartDelay(t_nut_long); 
      digitalWrite(RELAY_NUT_A, HIGH); digitalWrite(RELAY_NUT_B, HIGH);
      break;

    case 7: // Air Baku Short
      digitalWrite(RELAY_AIR, LOW); smartDelay(t_air_short); digitalWrite(RELAY_AIR, HIGH);
      break;
    case 8: // Air Baku Long
      digitalWrite(RELAY_AIR, LOW); smartDelay(t_air_long); digitalWrite(RELAY_AIR, HIGH);
      break;

    default:
      Serial.println("Aksi tidak dikenal!");
      break;
  }
}

// ==========================================
// MAIN LOOP
// ==========================================
void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  // Jika ada antrean perintah dari Python
  if (action_pending) {
    int aksiDikerjakan = current_action;
    unsigned long durasiNyala = 0;

    // Hitung durasi berdasarkan aksi
    if (aksiDikerjakan == 1 || aksiDikerjakan == 3) durasiNyala = t_ph_short;
    else if (aksiDikerjakan == 2 || aksiDikerjakan == 4) durasiNyala = t_ph_long;
    else if (aksiDikerjakan == 5) durasiNyala = t_nut_short;
    else if (aksiDikerjakan == 6) durasiNyala = t_nut_long;
    else if (aksiDikerjakan == 7) durasiNyala = t_air_short;
    else if (aksiDikerjakan == 8) durasiNyala = t_air_long;

    // 1. Jalankan Hardware
    eksekusiPompa(aksiDikerjakan);
    
    // 2. Kirim JSON LENGKAP ke InfluxDB via Telegraf
    String statusPayload = "{\"last_action\":" + String(aksiDikerjakan) + 
                           ",\"duration_ms\":" + String(durasiNyala) + 
                           ",\"status\":1}";
    mqttClient.publish(topic_status, statusPayload.c_str());
    
    // 3. Kirim "DONE" ke Python (biar Python lanjut ke homogenisasi)
    mqttClient.publish(topic_status, "DONE");
    
    Serial.print("Selesai! Data dikirim: ");
    Serial.println(statusPayload);

    action_pending = false;
  }
}