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
// 3. DURASI POMPA FISIK (Kompensasi Hardware Baru)
// Dihitung agar Volume tetap sama dengan Data Teori (2.4ml / 7.2ml)
// ==========================================
const unsigned long t_ph_s      = 2000;   // pH Up/Down (Tetap 2s)
const unsigned long t_ph_l      = 5000;   // pH Up/Down (Tetap 5s)
const unsigned long t_air_s     = 5000;   // Air Baku (Tetap 5s)
const unsigned long t_air_l     = 15000;  // Air Baku (Tetap 15s)
const unsigned long t_nut_a_s   = 1400;   // Nutrisi A (1.75 ml/s -> 1.4s)
const unsigned long t_nut_a_l   = 4110;   
const unsigned long t_nut_b_s   = 1200;   // Nutrisi B (2.0 ml/s -> 1.2s)
const unsigned long t_nut_b_l   = 3600;   
bool action_pending = false;
unsigned long lastReconnectAttempt = 0; // Timer non-blocking MQTT

// ==========================================
// ✅ FUNGSI PUBLISH MONITORING AKTUATOR
// Untuk visualisasi detail di Grafana/InfluxDB
// ==========================================
void publishAktuator(const char* nama_pompa, int aksi, float durasi_detik, int status) {
  char payload[256];
  char tampilan[64];

  // Membentuk string tampilan: misal "ON ph_up / 2.0s" atau "STANDBY"
  if (status == 1) {
    snprintf(tampilan, sizeof(tampilan), "ON %s / %.1fs", nama_pompa, durasi_detik);
  } else if (status == 0 && durasi_detik > 0.0) {
    snprintf(tampilan, sizeof(tampilan), "OFF %s / %.1fs", nama_pompa, durasi_detik);
  } else {
    snprintf(tampilan, sizeof(tampilan), "STANDBY");
  }

  // Baca status aktual 5 pin relay (Active LOW = ON, sehingga jika LOW nilainya 1)
  int st_ph_up = (digitalRead(RELAY_PH_UP) == LOW) ? 1 : 0;
  int st_ph_dn = (digitalRead(RELAY_PH_DN) == LOW) ? 1 : 0;
  int st_nut_a = (digitalRead(RELAY_NUT_A) == LOW) ? 1 : 0;
  int st_nut_b = (digitalRead(RELAY_NUT_B) == LOW) ? 1 : 0;
  int st_air   = (digitalRead(RELAY_AIR) == LOW)   ? 1 : 0;

  snprintf(payload, sizeof(payload),
    "{\"ph_up\":%d,\"ph_down\":%d,\"nutrisi_a\":%d,\"nutrisi_b\":%d,\"air_baku\":%d,\"aksi\":%d,\"tampilan\":\"%s\"}",
    st_ph_up, st_ph_dn, st_nut_a, st_nut_b, st_air, aksi, tampilan
  );
  
  mqttClient.publish(topic_aktuator, payload);
  Serial.print("[INFLUX] "); Serial.println(payload);
}

// ==========================================
// 8. LOGIKA EKSEKUSI RELAY (PINDAH KE BAWAH)
// ==========================================

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
  if (millis() - lastReconnectAttempt > 5000) {
    lastReconnectAttempt = millis();
    Serial.print("Konek ke MQTT...");
    String clientId = "ESP32_Aktuator_";
    clientId += String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("OK!");
      mqttClient.subscribe(topic_action); 
    } else {
      Serial.print("Gagal, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Coba lagi nanti.");
    }
  }
}

// ==========================================
// FUNGSI CALLBACK (Menangkap Perintah Python)
// ==========================================
void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  
  Serial.print("Pesan Masuk: "); Serial.println(msg);

  int colonIdx = msg.indexOf(':');
  if (colonIdx != -1) {
    int action = msg.substring(0, colonIdx).toInt();
    String tx_id = msg.substring(colonIdx + 1);

    if (tx_id != last_tx_id) {
      current_action = action;
      current_tx_id = tx_id;
      action_pending = true;
      Serial.printf("[NEW] Aksi %d | ID:%s\n", action, tx_id.c_str());
    } else {
      // Jika ID sama (Retry), langsung lapor DONE tanpa gerak pompa
      mqttClient.publish(topic_status, ("DONE:" + tx_id).c_str());
      Serial.printf("[RETRY] Skip Aksi karena ID %s sudah pernah diproses.\n", tx_id.c_str());
    }
  }
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
// ==========================================
// FUNGSI SMART DELAY (DENGAN HEARTBEAT STATUS)
// ==========================================
void smartDelay(unsigned long ms, const char* name, int action, float dur_sec, int status_val) {
  unsigned long start = millis();
  unsigned long lastPing = 0;
  
  while (millis() - start < ms) {
    if (!mqttClient.connected()) {
        reconnect(); 
    } else {
        mqttClient.loop();
    }
    
    // Heartbeat: Kirim ulang status setiap 1 detik agar terekam sebagai deret titik di InfluxDB
    if (millis() - lastPing > 1000) {
      publishAktuator(name, action, dur_sec, status_val);
      // Kirim juga ke topik status lama agar sinkron dengan Python/Grafana (0/1)
      mqttClient.publish(topic_status, String(status_val).c_str());
      lastPing = millis();
    }
    delay(10);
  }
}

// ==========================================
// 8. LOGIKA EKSEKUSI RELAY
// ==========================================
unsigned long lastStandbyPing = 0; // Untuk detak jantung siaga

void eksekusiPompa(int aksi) {
  Serial.print("Mengeksekusi Aksi: ");
  Serial.println(aksi);

  switch(aksi) {
    case 0: // Idle
      publishAktuator("idle", 0, 1.0, 0); 
      smartDelay(1000, "idle", 0, 1.0, 0); 
      break;
    
    case 1: // pH Up Short
      digitalWrite(RELAY_PH_UP, LOW); 
      publishAktuator("ph_up", 1, 2.0, 1);
      smartDelay(t_ph_short, "ph_up", 1, 2.0, 1); 
      digitalWrite(RELAY_PH_UP, HIGH);
      publishAktuator("ph_up", 1, 2.0, 0);
      break;
    case 2: // pH Up Long
      digitalWrite(RELAY_PH_UP, LOW); 
      publishAktuator("ph_up", 2, 5.0, 1);
      smartDelay(t_ph_long, "ph_up", 2, 5.0, 1); 
      digitalWrite(RELAY_PH_UP, HIGH);
      publishAktuator("ph_up", 2, 5.0, 0);
      break;

    case 3: // pH Down Short
      digitalWrite(RELAY_PH_DN, LOW); 
      publishAktuator("ph_down", 3, 2.0, 1);
      smartDelay(t_ph_short, "ph_down", 3, 2.0, 1); 
      digitalWrite(RELAY_PH_DN, HIGH);
      publishAktuator("ph_down", 3, 2.0, 0);
      break;
    case 4: // pH Down Long
      digitalWrite(RELAY_PH_DN, LOW); 
      publishAktuator("ph_down", 4, 5.0, 1);
      smartDelay(t_ph_long, "ph_down", 4, 5.0, 1); 
      digitalWrite(RELAY_PH_DN, HIGH);
      publishAktuator("ph_down", 4, 5.0, 0);
      break;

    case 5: // Nutrisi Short (A & B bersamaan)
      digitalWrite(RELAY_NUT_A, LOW); digitalWrite(RELAY_NUT_B, LOW); 
      publishAktuator("nutrisi_ab", 5, 2.0, 1);
      smartDelay(t_nut_short, "nutrisi_ab", 5, 2.0, 1); 
      digitalWrite(RELAY_NUT_A, HIGH); digitalWrite(RELAY_NUT_B, HIGH);
      publishAktuator("nutrisi_ab", 5, 2.0, 0);
      break;
    case 6: // Nutrisi Long (A & B bersamaan)
      digitalWrite(RELAY_NUT_A, LOW); digitalWrite(RELAY_NUT_B, LOW); 
      publishAktuator("nutrisi_ab", 6, 6.0, 1);
      smartDelay(t_nut_long, "nutrisi_ab", 6, 6.0, 1); 
      digitalWrite(RELAY_NUT_A, HIGH); digitalWrite(RELAY_NUT_B, HIGH);
      publishAktuator("nutrisi_ab", 6, 6.0, 0);
      break;

    case 7: // Air Baku Short
      digitalWrite(RELAY_AIR, LOW); 
      publishAktuator("air_baku", 7, 5.0, 1);
      smartDelay(t_air_short, "air_baku", 7, 5.0, 1); 
      digitalWrite(RELAY_AIR, HIGH);
      publishAktuator("air_baku", 7, 5.0, 0);
      break;
    case 8: // Air Baku Long
      digitalWrite(RELAY_AIR, LOW); 
      publishAktuator("air_baku", 8, 15.0, 1);
      smartDelay(t_air_long, "air_baku", 8, 15.0, 1); 
      digitalWrite(RELAY_AIR, HIGH);
      publishAktuator("air_baku", 8, 15.0, 0);
      break;

    default:
      Serial.println("Aksi tidak dikenal!");
      break;
  }
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  } else {
    mqttClient.loop();
  }

  if (action_pending) {
    // 1. Eksekusi Pompa (Di dalamnya sudah ada Heartbeat tiap 1 detik)
    eksekusiPompa(current_action);

    // 2. Kirim sinyal DONE dengan ID Transaksi
    last_tx_id = current_tx_id; // Simpan sebagai histori
    mqttClient.publish(topic_status, ("DONE:" + current_tx_id).c_str());
    Serial.printf("[MQTT] Sinyal DONE:%s dikirim ke RPi.\n", current_tx_id.c_str());

    action_pending = false;
    lastStandbyPing = millis(); // Reset waktu siaga setelah aksi
  } else {
    // Detak Jantung Siaga: Kirim status 0 setiap 10 detik agar database tidak kosong
    if (millis() - lastStandbyPing > 10000) {
      publishAktuator("standby", 0, 0.0, 0);
      mqttClient.publish(topic_status, "0");
      lastStandbyPing = millis();
      Serial.println("[HEARTBEAT] Status 0 terkirim (Siaga).");
    }
  }
}