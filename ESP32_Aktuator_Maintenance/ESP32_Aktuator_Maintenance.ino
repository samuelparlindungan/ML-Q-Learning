#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// 1. KONFIGURASI WIFI & MQTT
// ==========================================
const char* ssid        = "XinXun-9988";
const char* password    = "12345678";
const char* mqtt_server = "192.168.100.10";
const int   mqtt_port   = 1883;

const char* topic_action   = "hidroponik/action"; 
const char* topic_status   = "hidroponik/status"; 
const char* topic_mainten  = "hidroponik/maintenance"; // ✅ Topik Baru untuk CLI
const char* topic_aktuator = "hidroponik/aktuator";

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

// Durasi Fixed (Untuk Aksi 1-8)
const unsigned long T_PH_S  = 2000;   
const unsigned long T_PH_L  = 5000;   
const unsigned long T_NUT_S = 2000;   
const unsigned long T_NUT_L = 6000;   
const unsigned long T_AIR_S = 5000;   
const unsigned long T_AIR_L = 15000;  

// ==========================================
// 3. FUNGSI LOGIKA AKTUATOR
// ==========================================

void publishStatus() {
  char payload[256];
  int st[6];
  for (int i=1; i<=5; i++) st[i] = (digitalRead(PUMP_PINS[i]) == LOW) ? 1 : 0;

  snprintf(payload, sizeof(payload),
    "{\"ph_up\":%d,\"ph_down\":%d,\"nutrisi_a\":%d,\"nutrisi_b\":%d,\"air_baku\":%d,\"last_act\":%d}",
    st[1], st[2], st[3], st[4], st[5], lastActionID
  );
  mqttClient.publish(topic_aktuator, payload);
}

void triggerPump(int pumpIdx, unsigned long ms) {
  if (pumpIdx < 1 || pumpIdx > 5) return;
  if (ms == 0) { // Stop explicit
    digitalWrite(PUMP_PINS[pumpIdx], HIGH);
    stopTime[pumpIdx] = 0;
    return;
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
  
  Serial.printf("[MQTT] Topic: %s | Msg: %s\n", topic, msg.c_str());

  if (String(topic) == topic_action) {
    int action = msg.toInt();
    lastActionID = action;
    isAwaitingDone = true;

    switch(action) {
      case 0: break;
      case 1: triggerPump(1, T_PH_S); break;
      case 2: triggerPump(1, T_PH_L); break;
      case 3: triggerPump(2, T_PH_S); break;
      case 4: triggerPump(2, T_PH_L); break;
      case 5: triggerPump(4, T_NUT_S); triggerPump(5, T_NUT_S); break; // Nutrisi A & B
      case 6: triggerPump(4, T_NUT_L); triggerPump(5, T_NUT_L); break; // Nutrisi A & B
      case 7: triggerPump(3, T_AIR_S); break; // Air Baku
      case 8: triggerPump(3, T_AIR_L); break; // Air Baku
    }
  } 
  else if (String(topic) == topic_mainten) {
    // Format: "id duration_sec" e.g. "1 10"
    int spaceIdx = msg.indexOf(' ');
    if (spaceIdx != -1) {
      int id = msg.substring(0, spaceIdx).toInt();
      int dur = msg.substring(spaceIdx + 1).toInt();
      if (id == 0) stopAll();
      else triggerPump(id, (unsigned long)dur * 1000);
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
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32_Aktuator_Mainten_";
    clientId += String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
      mqttClient.subscribe(topic_action);
      mqttClient.subscribe(topic_mainten);
    } else {
      Serial.printf("failed, rc=%d try again in 5s\n", mqttClient.state());
      delay(5000);
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

// ==========================================
// 6. LOOP (CORE)
// ==========================================
void loop() {
  if (!mqttClient.connected()) reconnect();
  mqttClient.loop();

  unsigned long now = millis();
  bool anyPumpRunning = false;

  // 1. Check Non-Blocking Timers
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

  // 2. Handle "DONE" signal for Automated Actions
  if (isAwaitingDone && !anyPumpRunning) {
    mqttClient.publish(topic_status, "DONE");
    Serial.println("[MQTT] All pumps idle, sending DONE.");
    isAwaitingDone = false;
  }

  // 3. Serial Monitor Input (Maintenance)
  if (Serial.available() > 0) {
    int id = Serial.parseInt();
    int dur = Serial.parseInt();
    while (Serial.available() > 0) Serial.read(); // Clear buffer

    if (id == 0) stopAll();
    else if (id >= 1 && id <= 5 && dur > 0) {
      triggerPump(id, (unsigned long)dur * 1000);
    }
  }

  // 4. Status Heartbeat (2 Detik sekali)
  static unsigned long lastUpdate = 0;
  if (now - lastUpdate > 2000) {
    publishStatus();
    lastUpdate = now;
  }
}
