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
const char* topic_action   = "hidroponik/action"; 
const char* topic_status   = "hidroponik/status"; 
const char* topic_aktuator = "hidroponik/aktuator"; // ✅ Topik baru untuk InfluxDB

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ==========================================
// 2. DEFINISI PIN RELAY (Sesuai Hardware Anda)
// ==========================================
const int RELAY_PH_UP   = 14; 
const int RELAY_PH_DN   = 27; 
const int RELAY_AIR     = 26; 
const int RELAY_NUT_A   = 25; 
const int RELAY_NUT_B   = 33; 

// ==========================================
// 3. DURASI POMPA (ms)
// ==========================================
const unsigned long t_ph_short  = 2000;   
const unsigned long t_ph_long   = 5000;   
const unsigned long t_nut_short = 2000;   
const unsigned long t_nut_long  = 6000;   
const unsigned long t_air_short = 5000;   
const unsigned long t_air_long  = 15000;  

int current_action = -1;
bool action_pending = false;

// ==========================================
// ✅ FUNGSI PUBLISH MONITORING AKTUATOR
// Untuk visualisasi detail di Grafana/InfluxDB
// ==========================================
void publishAktuator(const char* nama_pompa, int aksi, float durasi_detik, int status) {
  char payload[256];
  char tampilan[32];

  // Membentuk string tampilan: misal "ON / 2.0s"
  if (status == 1) {
    snprintf(tampilan, sizeof(tampilan), "ON / %.1fs", durasi_detik);
  } else {
    snprintf(tampilan, sizeof(tampilan), "OFF / %.1fs", durasi_detik);
  }

  snprintf(payload, sizeof(payload),
    "{\"nama_pompa\":\"%s\",\"aksi\":%d,\"durasi_detik\":%.1f,\"status\":%d,\"tampilan\":\"%s\"}",
    nama_pompa, aksi, durasi_detik, status, tampilan
  );
  
  mqttClient.publish(topic_aktuator, payload);
  Serial.print("[INFLUX] "); Serial.println(payload);
}

// ==========================================
// FUNGSI SMART DELAY (Mencegah MQTT Putus)
// ==========================================
void smartDelay(unsigned long ms) {
  unsigned long start = millis();
  while (millis() - start < ms) {
    mqttClient.loop();
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
      publishAktuator("idle", 0, 1.0, 0); 
      smartDelay(1000); 
      break;
    
    case 1: // pH Up Short
      publishAktuator("ph_up", 1, 2.0, 1);
      digitalWrite(RELAY_PH_UP, LOW); smartDelay(t_ph_short); digitalWrite(RELAY_PH_UP, HIGH);
      publishAktuator("ph_up", 1, 2.0, 0);
      break;
    case 2: // pH Up Long
      publishAktuator("ph_up", 2, 5.0, 1);
      digitalWrite(RELAY_PH_UP, LOW); smartDelay(t_ph_long);  digitalWrite(RELAY_PH_UP, HIGH);
      publishAktuator("ph_up", 2, 5.0, 0);
      break;

    case 3: // pH Down Short
      publishAktuator("ph_down", 3, 2.0, 1);
      digitalWrite(RELAY_PH_DN, LOW); smartDelay(t_ph_short); digitalWrite(RELAY_PH_DN, HIGH);
      publishAktuator("ph_down", 3, 2.0, 0);
      break;
    case 4: // pH Down Long
      publishAktuator("ph_down", 4, 5.0, 1);
      digitalWrite(RELAY_PH_DN, LOW); smartDelay(t_ph_long);  digitalWrite(RELAY_PH_DN, HIGH);
      publishAktuator("ph_down", 4, 5.0, 0);
      break;

    case 5: // Nutrisi Short (A & B bersamaan)
      publishAktuator("nutrisi_ab", 5, 2.0, 1);
      digitalWrite(RELAY_NUT_A, LOW); digitalWrite(RELAY_NUT_B, LOW); 
      smartDelay(t_nut_short); 
      digitalWrite(RELAY_NUT_A, HIGH); digitalWrite(RELAY_NUT_B, HIGH);
      publishAktuator("nutrisi_ab", 5, 2.0, 0);
      break;
    case 6: // Nutrisi Long (A & B bersamaan)
      publishAktuator("nutrisi_ab", 6, 6.0, 1);
      digitalWrite(RELAY_NUT_A, LOW); digitalWrite(RELAY_NUT_B, LOW); 
      smartDelay(t_nut_long); 
      digitalWrite(RELAY_NUT_A, HIGH); digitalWrite(RELAY_NUT_B, HIGH);
      publishAktuator("nutrisi_ab", 6, 6.0, 0);
      break;

    case 7: // Air Baku Short
      publishAktuator("air_baku", 7, 5.0, 1);
      digitalWrite(RELAY_AIR, LOW); smartDelay(t_air_short); digitalWrite(RELAY_AIR, HIGH);
      publishAktuator("air_baku", 7, 5.0, 0);
      break;
    case 8: // Air Baku Long
      publishAktuator("air_baku", 8, 15.0, 1);
      digitalWrite(RELAY_AIR, LOW); smartDelay(t_air_long); digitalWrite(RELAY_AIR, HIGH);
      publishAktuator("air_baku", 8, 15.0, 0);
      break;

    default:
      Serial.println("Aksi tidak dikenal!");
      break;
  }
}

// ==========================================
// MAIN LOOP (VERSI LENGKAP: AKSI + DURASI + STATUS)
// ==========================================
void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  if (action_pending) {
    int aksiDikerjakan = current_action;
    unsigned long durasiNyala = 0;

    // A. Tentukan durasi otomatis untuk dikirim ke Database
    if (aksiDikerjakan == 1 || aksiDikerjakan == 3) durasiNyala = t_ph_short;
    else if (aksiDikerjakan == 2 || aksiDikerjakan == 4) durasiNyala = t_ph_long;
    else if (aksiDikerjakan == 5) durasiNyala = t_nut_short;
    else if (aksiDikerjakan == 6) durasiNyala = t_nut_long;
    else if (aksiDikerjakan == 7) durasiNyala = t_air_short;
    else if (aksiDikerjakan == 8) durasiNyala = t_air_long;
    else durasiNyala = 0; // Untuk aksi 0 (Idle)

    // 1. Kirim Sinyal ON (Status 1) - Pompa Mulai
    String statusOn = "{\"last_action\":" + String(aksiDikerjakan) + 
                      ", \"duration_ms\":" + String(durasiNyala) + 
                      ", \"status\":1}";
    mqttClient.publish(topic_status, statusOn.c_str());
    Serial.print("Pompa ON: "); Serial.println(statusOn);

    // 2. Jalankan Hardware (Bloking sesuai durasi)
    eksekusiPompa(aksiDikerjakan);
    
    // 3. Kirim Sinyal OFF (Status 0) - Pompa Selesai
    String statusOff = "{\"last_action\":" + String(aksiDikerjakan) + 
                       ", \"duration_ms\":" + String(durasiNyala) + 
                       ", \"status\":0}";
    mqttClient.publish(topic_status, statusOff.c_str());
    Serial.print("Pompa OFF: "); Serial.println(statusOff);
    
    // 4. Kirim "DONE" ke Python (Sinyal untuk Homogenisasi)
    mqttClient.publish(topic_status, "DONE");
    
    action_pending = false;
  }
}