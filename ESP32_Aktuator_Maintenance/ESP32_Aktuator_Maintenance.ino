#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==========================================
// 1. KONFIGURASI WIFI & MQTT
// ==========================================
const char* ssid        = "XinXun-9988";
const char* password    = "12345678";
const char* mqtt_server = "192.168.100.10";
const int   mqtt_port   = 1883;

const char* topic_action   = "hidroponik/action"; 
const char* topic_status   = "hidroponik/status"; 
const char* topic_mainten  = "hidroponik/maintenance"; 
const char* topic_aktuator = "hidroponik/aktuator";
const char* topic_sensor   = "hidroponik/sensor";    // ✅ Unsur Safety

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ==========================================
// 2. PIN & POMPA (Indeks 1-5)
// ==========================================
const int PUMP_PINS[6] = {0, 14, 27, 26, 25, 33}; 
const char* PUMP_NAMES[6] = {"", "pH UP", "pH DOWN", "AIR BAKU", "NUTRISI A", "NUTRISI B"};

// Variabel Kontrol Non-Blocking
unsigned long stopTime[6] = {0, 0, 0, 0, 0, 0};
int lastActionID = -1;
bool isAwaitingDone = false;
String last_tx_id = "INIT";
String current_tx_id = "";
String tampilan = "STANDBY"; // Nilai default untuk InfluxDB
unsigned long lastReconnectAttempt = 0; // Timer non-blocking MQTT

// Variabel Safety (Update dari MQTT Sensor)
float level_box = 20.0; // Default aman (Liter)
float level_tabung[6] = {0, 500, 500, 500, 500, 500}; // T1-T5 (mL)
const float AMBANG_BOX = 5.0;   // Minimal 5L air
const float AMBANG_TABUNG = 50.0; // Minimal 50mL nutrisi/pH

// Durasi Fisik Baru (Kompensasi Hardware Baru)
const unsigned long T_PH_S    = 2000;   
const unsigned long T_PH_L    = 5000;   
const unsigned long T_NUT_A_S = 1400;   // Nutrisi A (1.75 ml/s -> 1.4s)
const unsigned long T_NUT_A_L = 4110;   
const unsigned long T_NUT_B_S = 1200;   // Nutrisi B (2.0 ml/s -> 1.2s)
const unsigned long T_NUT_B_L = 3600;   
const unsigned long T_AIR_S   = 5000;   
const unsigned long T_AIR_L   = 15000;  

// ==========================================
// 3. FUNGSI LOGIKA AKTUATOR
// ==========================================

void publishStatus() {
  StaticJsonDocument<256> doc;
  doc["ph_up"] = (digitalRead(PUMP_PINS[1]) == LOW) ? 1 : 0;
  doc["ph_down"] = (digitalRead(PUMP_PINS[2]) == LOW) ? 1 : 0;
  doc["air_baku"] = (digitalRead(PUMP_PINS[3]) == LOW) ? 1 : 0;
  doc["nutrisi_a"] = (digitalRead(PUMP_PINS[4]) == LOW) ? 1 : 0;
  doc["nutrisi_b"] = (digitalRead(PUMP_PINS[5]) == LOW) ? 1 : 0;
  doc["last_act"] = lastActionID;
  doc["box"] = level_box;
  doc["tampilan"] = tampilan; // ✅ Agar Grafana tetap sinkron 2s/6s

  char payload[256];
  serializeJson(doc, payload);
  mqttClient.publish(topic_aktuator, payload);
}

void triggerPump(int pumpIdx, unsigned long ms, bool force = false) {
  if (pumpIdx < 1 || pumpIdx > 5) return;
  
  if (ms == 0) { // Stop explicit
    digitalWrite(PUMP_PINS[pumpIdx], HIGH);
    stopTime[pumpIdx] = 0;
    return;
  }

  // --- SAFETY INTERLOCK CHECK ---
  if (!force) {
    if (level_box < AMBANG_BOX) {
      Serial.println("⚠️ SAFETY: Tandon Utama KRITIS! Pompa Dibatalkan.");
      return;
    }
    if (level_tabung[pumpIdx] < AMBANG_TABUNG) {
      Serial.printf("⚠️ SAFETY: Tabung %s KOSONG! Pompa Dibatalkan.\n", PUMP_NAMES[pumpIdx]);
      return;
    }
  } else {
    Serial.println("⚙️ MAINTENANCE: Safety di-BYPASS.");
  }

  digitalWrite(PUMP_PINS[pumpIdx], LOW); // ON
  stopTime[pumpIdx] = millis() + ms;
  Serial.printf("[POMPA] %s ON selama %lu ms\n", PUMP_NAMES[pumpIdx], ms);
}

void stopAll() {
  Serial.println("[SYSTEM] EMERGENCY STOP!");
  for (int i=1; i<=5; i++) {
    digitalWrite(PUMP_PINS[i], HIGH);
    stopTime[i] = 0;
  }
  isAwaitingDone = false;
  mqttClient.publish(topic_status, "STOPPED");
}

// ==========================================
// 4. MQTT CALLBACK
// ==========================================
void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];
  
  // A. UPDATE DATA SENSOR (SAFETY BASE)
  if (String(topic) == topic_sensor) {
    StaticJsonDocument<512> doc;
    if (!deserializeJson(doc, payload, length)) {
      level_box = doc["box"];
      level_tabung[1] = doc["t1"]; // pH Up
      level_tabung[2] = doc["t2"]; // pH Down
      level_tabung[3] = doc["t3"]; // Air Baku
      level_tabung[4] = doc["t4"]; // Nutrisi A
      level_tabung[5] = doc["t5"]; // Nutrisi B
    }
    return; 
  }

  Serial.printf("[MQTT] Topic: %s | Msg: %s\n", topic, msg.c_str());

  // B. EKSEKUSI OTOMATIS (DENGAN SAFETY)
  if (String(topic) == topic_action) {
    int colonIdx = msg.indexOf(':');
    if (colonIdx != -1) {
      int action = msg.substring(0, colonIdx).toInt();
      String tx_id = msg.substring(colonIdx + 1);

      if (tx_id != last_tx_id) {
        current_tx_id = tx_id;
        isAwaitingDone = true;
        Serial.printf("[NEW] Aksi %d | ID:%s\n", action, tx_id.c_str());
        
        switch(action) {
          case 0: tampilan = "IDLE"; break;
          case 1: tampilan = "ON ph_up / 2.0s"; triggerPump(1, T_PH_S, true); break;
          case 2: tampilan = "ON ph_up / 5.0s"; triggerPump(1, T_PH_L, true); break;
          case 3: tampilan = "ON ph_down / 2.0s"; triggerPump(2, T_PH_S, true); break;
          case 4: tampilan = "ON ph_down / 5.0s"; triggerPump(2, T_PH_L, true); break;
          case 5: tampilan = "ON nutrisi_ab / 2.0s"; triggerPump(4, T_NUT_A_S, true); triggerPump(5, T_NUT_B_S, true); break;
          case 6: tampilan = "ON nutrisi_ab / 6.0s"; triggerPump(4, T_NUT_A_L, true); triggerPump(5, T_NUT_B_L, true); break;
          case 7: tampilan = "ON air_baku / 5.0s"; triggerPump(3, T_AIR_S, true); break;
          case 8: tampilan = "ON air_baku / 15.0s"; triggerPump(3, T_AIR_L, true); break;
        }
      } else {
        // Retry detected
        mqttClient.publish(topic_status, ("DONE:" + tx_id).c_str());
        Serial.printf("[RETRY] Skip Aksi karena ID %s sudah pernah diproses.\n", tx_id.c_str());
      }
    }
  } 
  // C. EKSEKUSI MAINTENANCE (BYPASS SAFETY)
  else if (String(topic) == topic_mainten) {
    int spaceIdx = msg.indexOf(' ');
    if (spaceIdx != -1) {
      int id = msg.substring(0, spaceIdx).toInt();
      int dur = msg.substring(spaceIdx + 1).toInt();
      if (id == 0) { stopAll(); tampilan = "STOPPED"; }
      else {
        tampilan = "ON Pump " + String(id) + " / " + String(dur) + "s";
        triggerPump(id, (unsigned long)dur * 1000, true); // true = force bypass
      }
    }
  }
}

// ==========================================
// 5. SETUP & WIFI
// ==========================================
void setup_wifi() {
  Serial.print("\nConnecting to "); Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi Connected!");
}

void reconnect() {
  // Hanya mencoba koneksi jika sudah lewat 5 detik dari percobaan terakhir
  if (millis() - lastReconnectAttempt > 5000) {
    lastReconnectAttempt = millis();
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32_Aktuator_Mainten_";
    clientId += String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
      mqttClient.subscribe(topic_action);
      mqttClient.subscribe(topic_mainten);
      mqttClient.subscribe(topic_sensor);
    } else {
      Serial.printf("failed, rc=%d\n", mqttClient.state());
    }
  }
}

void setup() {
  Serial.begin(115200);
  for (int i=1; i<=5; i++) {
    pinMode(PUMP_PINS[i], OUTPUT);
    digitalWrite(PUMP_PINS[i], HIGH);
  }
  setup_wifi();
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect(); // Sekarang non-blocking
  } else {
    mqttClient.loop();
  }

  unsigned long now = millis();
  bool anyPumpRunning = false;

  for (int i=1; i<=5; i++) {
    if (stopTime[i] > 0) {
      if (now >= stopTime[i]) {
        digitalWrite(PUMP_PINS[i], HIGH);
        stopTime[i] = 0;
        Serial.printf("[POMPA] %s OFF (Auto)\n", PUMP_NAMES[i]);
      } else {
        anyPumpRunning = true;
      }
    }
  }

  if (!anyPumpRunning && tampilan != "STANDBY") {
    tampilan = "STANDBY";
  }

  if (isAwaitingDone && !anyPumpRunning) {
    last_tx_id = current_tx_id;
    mqttClient.publish(topic_status, ("DONE:" + current_tx_id).c_str());
    Serial.printf("[MQTT] Sinyal DONE:%s dikirim ke RPi.\n", current_tx_id.c_str());
    isAwaitingDone = false;
  }

  // Serial Maintenance juga BYPASS Safety
  if (Serial.available() > 0) {
    int id = Serial.parseInt();
    int dur = Serial.parseInt();
    while (Serial.available() > 0) Serial.read(); 

    if (id == 0) stopAll();
    else if (id >= 1 && id <= 5 && dur > 0) {
      triggerPump(id, (unsigned long)dur * 1000, true); // true = force bypass
    }
  }

  static unsigned long lastUpdate = 0;
  if (now - lastUpdate > 2000) {
    publishStatus();
    lastUpdate = now;
  }
}
