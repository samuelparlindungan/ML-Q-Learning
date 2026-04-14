#include <EEPROM.h>
#include "DFRobot_PH.h"
#include "DFRobot_EC.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// WIFI & MQTT
// ==========================================
const char* WIFI_SSID   = "XinXun-9988";
const char* WIFI_PASS   = "12345678";
const char* MQTT_SERVER = "192.168.100.10";
const int   MQTT_PORT   = 1883;
const char* MQTT_TOPIC  = "hidroponik/sensor";

WiFiClient espClient;
PubSubClient client(espClient);

// ==========================================
// PIN
// ==========================================
#define PH_PIN   34
#define EC_PIN   35
#define DS_PIN    4
#define FL_PIN   13

#define T1_TRIG 12
#define T1_ECHO 32
#define T2_TRIG 14
#define T2_ECHO 27
#define T3_TRIG 26
#define T3_ECHO 25
#define T4_TRIG  2
#define T4_ECHO 16
#define T5_TRIG 18
#define T5_ECHO 19
#define BX_TRIG 33
#define BX_ECHO 17

// ==========================================
// KONSTANTA ADC pH & EC
// ==========================================
#define ESP_ADC_VREF 3300.0f
#define ESP_ADC_RES  4096.0f

// ==========================================
// KONSTANTA TABUNG 1L
// Diameter dalam = 8.3cm → r = 4.15cm
// Luas alas = π × 4.15² = 54.11 cm²
// Offset = tinggi dari dasar ke mata sensor = 16.2cm
// ==========================================
#define T_LUAS  54.11f
#define T_MAX   1000.0f

float offsetTabung[5] = {
  16.2,  // T1 — pH Up
  16.2,  // T2 — pH Down
  16.2,  // T3 — Air
  16.2,  // T4 — Nutrisi A
  16.2   // T5 — Nutrisi B
};

// ==========================================
// KONSTANTA BOX TANDON
// Luas empiris dari 15L = tinggi 17.2cm
// Luas = 15000 / 17.2 = 872.09 cm²
// offsetBox = jarak sensor ke dasar = 22.0cm
// ==========================================
#define B_LUAS   872.09f
#define B_OFFSET 22.0f
#define B_MAX    19.0f

// ==========================================
// KONSTANTA FLOW METER
// YF-S201: 7.5 pulsa/detik = 1 L/menit
// ==========================================
#define FLOW_FACTOR 7.5f

// ==========================================
// OBJEK SENSOR
// ==========================================
DFRobot_PH ph;
DFRobot_EC ec;
OneWire ow(DS_PIN);
DallasTemperature objDS(&ow);

// ==========================================
// VARIABEL pH & EC
// ==========================================
float voltagePH = 0, voltageEC = 0;
float phValue   = 7.0f;
float ecValue   = 0.0f;
float temperature = 25.0f;

// ==========================================
// VARIABEL FLOW METER
// ==========================================
volatile unsigned long pulsaFlow = 0;
float flowLM     = 0;
float totalLiter = 0;
unsigned long tFlowHitung = 0;

// ==========================================
// VARIABEL ULTRASONIK
// ==========================================
float lastTabung[5] = {0,0,0,0,0};
float lastBox = 0;

// ==========================================
// VARIABEL WIFI
// ==========================================
unsigned long tWifiRetry = 0;
unsigned long tMqttRetry = 0;
bool wifiConnected = false;

// ==========================================
// ISR FLOW METER
// ==========================================
void IRAM_ATTR onPulseFlow() {
  pulsaFlow++;
}

// ==========================================
// HITUNG FLOW — dipanggil tiap loop
// ==========================================
void hitungFlow() {
  unsigned long sekarang = millis();
  unsigned long dt = sekarang - tFlowHitung;
  if (dt < 1000) return;

  noInterrupts();
  unsigned long pulsa = pulsaFlow;
  pulsaFlow = 0;
  interrupts();

  tFlowHitung = sekarang;

  float pulsePerDetik = (float)pulsa / (dt / 1000.0f);
  flowLM = pulsePerDetik / FLOW_FACTOR;
  if (flowLM < 0.05f) flowLM = 0;

  totalLiter += flowLM * (dt / 60000.0f);
}

// ==========================================
// WiFi
// ==========================================
void setupWifi() {
  Serial.print("Konek WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t = millis();
  while (WiFi.status() != WL_CONNECTED && millis()-t < 15000) {
    delay(500); Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println(" OK! IP: " + WiFi.localIP().toString());
  } else {
    wifiConnected = false;
    Serial.println(" GAGAL!");
  }
}

void cekWifi() {
  if (WiFi.status() == WL_CONNECTED) { wifiConnected = true; return; }
  wifiConnected = false;
  if (millis() - tWifiRetry < 10000) return;
  tWifiRetry = millis();
  Serial.print("WiFi putus! Reconnect");
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t = millis();
  while (WiFi.status() != WL_CONNECTED && millis()-t < 8000) {
    delay(500); Serial.print(".");
  }
  wifiConnected = (WiFi.status() == WL_CONNECTED);
  Serial.println(wifiConnected ? " OK!" : " Gagal...");
}

void cekMQTT() {
  if (!wifiConnected || client.connected()) return;
  if (millis() - tMqttRetry < 5000) return;
  tMqttRetry = millis();
  Serial.print("MQTT konek...");
  String id = "ESP32_Hidro_" + String((uint32_t)ESP.getEfuseMac(), HEX);
  if (client.connect(id.c_str())) Serial.println(" OK!");
  else Serial.printf(" GAGAL rc=%d\n", client.state());
}

// ==========================================
// ULTRASONIK: Single ping
// ==========================================
float singlePing(int trig, int echo, unsigned long timeout) {
  digitalWrite(trig, LOW);  delayMicroseconds(2);
  digitalWrite(trig, HIGH); delayMicroseconds(10);
  digitalWrite(trig, LOW);
  long d = pulseIn(echo, HIGH, timeout);
  if (!d) return -1.0f;
  return d * 0.0343f / 2.0f;
}

// ==========================================
// ULTRASONIK: Trimmed mean
// ==========================================
float trimmedMean(float* s, int n, int trim) {
  for (int i = 0; i < n-1; i++)
    for (int j = i+1; j < n; j++)
      if (s[i] > s[j]) { float t = s[i]; s[i] = s[j]; s[j] = t; }
  int start = min(trim, n/4);
  int end   = n - start;
  float sum = 0; int cnt = 0;
  for (int i = start; i < end; i++) { sum += s[i]; cnt++; }
  return cnt > 0 ? sum/cnt : -1.0f;
}

// ==========================================
// ULTRASONIK: Baca tabung 1L
// tinggiAir = offsetTabung - jarak
// volume    = tinggiAir × T_LUAS
// ==========================================
float bacaTabung(int trig, int echo, float &lastVal, int idx) {
  const int N = 11, TRIM = 3, MIN_VALID = 4;
  float s[N]; int n = 0;

  for (int i = 0; i < N; i++) {
    float j = singlePing(trig, echo, 35000);
    delay(15);
    if (j < 0) continue;
    if (j < 1.0f || j > offsetTabung[idx] + 0.5f) continue;
    s[n++] = j;
  }

  if (n < MIN_VALID) return lastVal;

  float jarak = trimmedMean(s, n, TRIM);
  if (jarak < 0) return lastVal;

  float tinggi = offsetTabung[idx] - jarak;
  if (tinggi < 0) tinggi = 0;

  float vol = constrain(tinggi * T_LUAS, 0.0f, T_MAX);

  if (lastVal > 0) {
    float d = vol - lastVal;
    if (d >  150.0f) vol = lastVal + 150.0f;
    if (d < -150.0f) vol = lastVal - 150.0f;
  }

  if (vol < 10.0f) vol = 0.0f;

  lastVal = vol;
  return vol;
}

// ==========================================
// ULTRASONIK: Baca box tandon
// tinggiAir = B_OFFSET - jarak
// volume    = tinggiAir × B_LUAS / 1000 (Liter)
// ==========================================
float bacaBox(int trig, int echo) {
  const int N = 11, TRIM = 3, MIN_VALID = 4;
  float s[N]; int n = 0;

  for (int i = 0; i < N; i++) {
    float j = singlePing(trig, echo, 40000);
    delay(15);
    if (j < 0) continue;
    if (j < 1.5f || j > B_OFFSET + 0.5f) continue;
    s[n++] = j;
  }

  if (n < MIN_VALID) {
    Serial.printf("[Box] Hanya %d sampel valid\n", n);
    return lastBox;
  }

  float jarak = trimmedMean(s, n, TRIM);
  if (jarak < 0) return lastBox;

  float tinggi = B_OFFSET - jarak;
  if (tinggi < 0) tinggi = 0;

  float vol = constrain((tinggi * B_LUAS) / 1000.0f, 0.0f, B_MAX);

  if (lastBox > 0) {
    float d = vol - lastBox;
    if (d >  0.3f) vol = lastBox + 0.3f;
    if (d < -0.3f) vol = lastBox - 0.3f;
  }

  if (vol < 0.05f) vol = 0.0f;

  lastBox = vol;
  return vol;
}

// ==========================================
// SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(500);

  // Pin ultrasonik
  int trig[] = {T1_TRIG,T2_TRIG,T3_TRIG,T4_TRIG,T5_TRIG,BX_TRIG};
  int echo[] = {T1_ECHO,T2_ECHO,T3_ECHO,T4_ECHO,T5_ECHO,BX_ECHO};
  for (int i = 0; i < 6; i++) {
    pinMode(trig[i], OUTPUT);
    pinMode(echo[i], INPUT);
  }

  // Flow meter
  pinMode(FL_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FL_PIN), onPulseFlow, FALLING);
  tFlowHitung = millis();

  // EEPROM & sensor kimia
  EEPROM.begin(64);
  ph.begin();
  ec.begin();
  objDS.begin();

  // WiFi & MQTT
  setupWifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setKeepAlive(60);
  client.setSocketTimeout(10);

  Serial.println("============================================");
  Serial.println("   SISTEM HIDROPONIK MONITORING AKTIF      ");
  Serial.println("   Kalibrasi pH : enterph -> calph -> exitph");
  Serial.println("   Kalibrasi EC : enterec -> calec -> exitec");
  Serial.println("============================================");
  Serial.printf("T_LUAS=%.2fcm2 | offset=%.1fcm\n", T_LUAS, offsetTabung[0]);
  Serial.printf("B_LUAS=%.2fcm2 | B_OFFSET=%.1fcm | B_MAX=%.1fL\n",
                B_LUAS, B_OFFSET, B_MAX);
}

// ==========================================
// LOOP
// ==========================================
void loop() {
  static unsigned long tSensor = 0;  // pH & EC tiap 1 detik
  static unsigned long tSend   = 0;  // kirim MQTT tiap 5 detik

  // Jaga koneksi
  cekWifi();
  cekMQTT();
  client.loop();

  // Hitung flow non-blocking
  hitungFlow();

  // ── pH & EC: baca setiap 1 detik (dari kode referensi) ──
  if (millis() - tSensor > 1000UL) {
    tSensor = millis();

    // Baca suhu untuk kompensasi
    objDS.requestTemperatures();
    float t2 = objDS.getTempCByIndex(0);
    if (t2 != DEVICE_DISCONNECTED_C) temperature = t2;

    // Baca pH
    int adcPH = analogRead(PH_PIN);
    voltagePH = (float)adcPH / ESP_ADC_RES * ESP_ADC_VREF;
    phValue   = ph.readPH(voltagePH, temperature);

    // Baca EC
    int adcEC = analogRead(EC_PIN);
    voltageEC = (float)adcEC / ESP_ADC_RES * ESP_ADC_VREF;
    ecValue   = ec.readEC(voltageEC, temperature) * 1000.0f; // mS/cm → uS/cm
  }

  // ── Kalibrasi wajib jalan terus ──
  ph.calibration(voltagePH, temperature);
  ec.calibration(voltageEC, temperature);

  // ── Baca ultrasonik & kirim MQTT setiap 5 detik ──
  if (millis() - tSend >= 5000UL) {
    tSend = millis();

    // Baca ultrasonik
    float v1 = bacaTabung(T1_TRIG,T1_ECHO,lastTabung[0],0); delay(50);
    float v2 = bacaTabung(T2_TRIG,T2_ECHO,lastTabung[1],1); delay(50);
    float v3 = bacaTabung(T3_TRIG,T3_ECHO,lastTabung[2],2); delay(50);
    float v4 = bacaTabung(T4_TRIG,T4_ECHO,lastTabung[3],3); delay(50);
    float v5 = bacaTabung(T5_TRIG,T5_ECHO,lastTabung[4],4); delay(50);
    float vb = bacaBox(BX_TRIG, BX_ECHO);

    // Serial monitor
    Serial.println("==========================================");
    Serial.printf("WiFi:%s | MQTT:%s\n",
      WiFi.status()==WL_CONNECTED ? "OK" : "PUTUS",
      client.connected() ? "OK" : "PUTUS");
    Serial.printf("pH Volt:%.0f | pH:%.2f\n", voltagePH, phValue);
    Serial.printf("EC Volt:%.0f | EC:%.0f uS/cm\n", voltageEC, ecValue);
    Serial.printf("Suhu:%.1f C\n", temperature);
    Serial.printf("T1:%.0f T2:%.0f T3:%.0f T4:%.0f T5:%.0f mL\n",
                  v1, v2, v3, v4, v5);
    Serial.printf("Box:%.2fL (%.1f%%)\n", vb, (vb/B_MAX)*100.0f);
    Serial.printf("Flow:%.2f L/mnt | Total:%.3f L\n", flowLM, totalLiter);
    Serial.println("==========================================");

    // Publish MQTT
    if (client.connected()) {
      char payload[300];
      snprintf(payload, sizeof(payload),
        "{\"ph\":%.2f,\"ec\":%.0f,\"suhu\":%.2f,"
        "\"t1\":%.0f,\"t2\":%.0f,\"t3\":%.0f,"
        "\"t4\":%.0f,\"t5\":%.0f,\"box\":%.2f,"
        "\"flow\":%.2f,\"total\":%.3f}",
        phValue, ecValue, temperature,
        v1, v2, v3, v4, v5, vb,
        flowLM, totalLiter);
      Serial.printf("MQTT:%s\n", client.publish(MQTT_TOPIC,payload) ? "OK" : "GAGAL");
    } else {
      Serial.println("MQTT:Skip");
    }
  }
}