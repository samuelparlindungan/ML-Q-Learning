#include <EEPROM.h>
#include "DFRobot_PH.h"
#include "DFRobot_EC.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <NTPClient.h>      // Library Tambahan untuk Latensi
#include <WiFiUdp.h>        // Library Tambahan untuk Latensi

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

// Konfigurasi NTP untuk Latensi (GMT+7 = 25200 detik)
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "id.pool.ntp.org", 0);

// ==========================================
// PIN & KONSTANTA (Sesuai Kode Asli Josh)
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

#define ESP_ADC_VREF 3300.0f
#define ESP_ADC_RES  4096.0f
#define T_LUAS  54.11f
#define T_MAX   1000.0f
#define B_LUAS   872.09f
#define B_OFFSET 22.0f
#define B_MAX    19.0f
#define FLOW_FACTOR 7.5f

float offsetTabung[5] = {16.2, 16.2, 16.2, 16.2, 16.2};
DFRobot_PH ph;
DFRobot_EC ec;
OneWire ow(DS_PIN);
DallasTemperature objDS(&ow);

float voltagePH = 0, voltageEC = 0, phValue = 7.0f, ecValue = 0.0f, temperature = 25.0f;
volatile unsigned long pulsaFlow = 0;
float flowLM = 0, totalLiter = 0;
unsigned long tFlowHitung = 0;
float lastTabung[5] = {0,0,0,0,0}, lastBox = 0;
unsigned long tWifiRetry = 0, tMqttRetry = 0;
bool wifiConnected = false;

// ==========================================
// FUNGSI SISTEM (Sesuai Kode Asli Josh)
// ==========================================
void IRAM_ATTR onPulseFlow() { pulsaFlow++; }

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

void setupWifi() {
  Serial.print("Konek WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t = millis();
  while (WiFi.status() != WL_CONNECTED && millis()-t < 15000) { delay(500); Serial.print("."); }
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println(" OK! IP: " + WiFi.localIP().toString());
    timeClient.begin(); // Mulai NTP setelah WiFi konek
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
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

void cekMQTT() {
  if (!client.connected() && wifiConnected) {
    if (millis() - tMqttRetry > 5000) {
      tMqttRetry = millis();
      if (client.connect("ESP32_Hidroponik")) Serial.println("MQTT OK!");
    }
  }
}

float singlePing(int trig, int echo, unsigned long timeout) {
  digitalWrite(trig, LOW); delayMicroseconds(2);
  digitalWrite(trig, HIGH); delayMicroseconds(10);
  digitalWrite(trig, LOW);
  unsigned long duration = pulseIn(echo, HIGH, timeout);
  if (duration == 0) return -1;
  return (duration / 2.0f) * 0.0343f;
}

float getMedian(float* array, int length) {
  for (int i = 0; i < length - 1; i++) {
    for (int j = i + 1; j < length; j++) {
      if (array[j] < array[i]) { float temp = array[i]; array[i] = array[j]; array[j] = temp; }
    }
  }
  return (length % 2 == 1) ? array[length / 2] : (array[(length / 2) - 1] + array[length / 2]) / 2.0f;
}

float bacaTabung(int trig, int echo, float &lastVal, int idx) {
  const int N = 5; float s[N]; int n = 0;
  for (int i = 0; i < N; i++) {
    float j = singlePing(trig, echo, 35000); delay(40);
    if (j >= 0.5f && j <= offsetTabung[idx] + 1.0f) s[n++] = j;
  }
  if (n < 3) return lastVal;
  float vol = constrain((offsetTabung[idx] - getMedian(s, n)) * T_LUAS, 0.0f, T_MAX);
  lastVal = vol; return vol;
}

float bacaBox(int trig, int echo) {
  const int N = 5; float s[N]; int n = 0;
  for (int i = 0; i < N; i++) {
    float j = singlePing(trig, echo, 40000); delay(40);
    if (j >= 1.0f && j <= B_OFFSET + 1.0f) s[n++] = j;
  }
  if (n < 3) return lastBox;
  float vol = constrain(((B_OFFSET - getMedian(s, n)) * B_LUAS) / 1000.0f, 0.0f, B_MAX);
  lastBox = vol; return vol;
}

// ==========================================
// SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  int trig[] = {T1_TRIG,T2_TRIG,T3_TRIG,T4_TRIG,T5_TRIG,BX_TRIG};
  int echo[] = {T1_ECHO,T2_ECHO,T3_ECHO,T4_ECHO,T5_ECHO,BX_ECHO};
  for (int i = 0; i < 6; i++) { pinMode(trig[i], OUTPUT); pinMode(echo[i], INPUT); }
  pinMode(FL_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FL_PIN), onPulseFlow, FALLING);
  EEPROM.begin(64);
  ph.begin(); ec.begin(); objDS.begin();
  setupWifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
}

// ==========================================
// LOOP
// ==========================================
void loop() {
  static unsigned long tSensor = 0;
  static unsigned long tSend   = 0;

  cekWifi(); cekMQTT(); client.loop();
  hitungFlow();

  if (millis() - tSensor > 1000UL) {
    tSensor = millis();
    objDS.requestTemperatures();
    float t2 = objDS.getTempCByIndex(0);
    if (t2 != DEVICE_DISCONNECTED_C) temperature = t2;
    long totalAdcPH = 0, totalAdcEC = 0;
    for(int i = 0; i < 40; i++) { totalAdcPH += analogRead(PH_PIN); totalAdcEC += analogRead(EC_PIN); delay(2); }
    voltagePH = (float)(totalAdcPH / 40) / ESP_ADC_RES * ESP_ADC_VREF;
    phValue   = ph.readPH(voltagePH, temperature);
    voltageEC = ((float)(totalAdcEC / 40) / ESP_ADC_RES * ESP_ADC_VREF) * 1.4545f;
    ecValue   = ec.readEC(voltageEC, temperature) * 1000.0f;
  }

  ph.calibration(voltagePH, temperature);
  ec.calibration(voltageEC, temperature);

  if (millis() - tSend >= 5300UL) {
    tSend = millis();
    float v1 = bacaTabung(T1_TRIG,T1_ECHO,lastTabung[0],0);
    float v2 = bacaTabung(T2_TRIG,T2_ECHO,lastTabung[1],1);
    float v3 = bacaTabung(T3_TRIG,T3_ECHO,lastTabung[2],2);
    float v4 = bacaTabung(T4_TRIG,T4_ECHO,lastTabung[3],3);
    float v5 = bacaTabung(T5_TRIG,T5_ECHO,lastTabung[4],4);
    float vb = bacaBox(BX_TRIG, BX_ECHO);

    if (client.connected()) {
      timeClient.update();
      // Hitung milidetik untuk Timestamp
      unsigned long long timestamp = ((unsigned long long)timeClient.getEpochTime() * 1000ULL) + (millis() % 1000ULL);

      char payload[600];
      snprintf(payload, sizeof(payload),
        "{\"ph\":%.2f,\"ec\":%.0f,\"suhu\":%.2f,\"t1\":%.0f,\"t2\":%.0f,\"t3\":%.0f,\"t4\":%.0f,\"t5\":%.0f,\"box\":%.2f,\"flow\":%.2f,\"total\":%.3f,\"timestamp\":%llu}",
        phValue, ecValue, temperature, v1, v2, v3, v4, v5, vb, flowLM, totalLiter, timestamp);
      
      client.publish(MQTT_TOPIC, payload);
      Serial.println("Data Sent with Timestamp!");
    }
  }
}