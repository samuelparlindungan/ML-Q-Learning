#include <EEPROM.h>
#include "DFRobot_PH.h"
#include "DFRobot_EC.h"
#include <OneWire.h>
#include <DallasTemperature.h>

// ==========================================
// KONFIGURASI PIN (SESUAIKAN JIKA BERBEDA)
// ==========================================
#define PH_PIN 34    
#define EC_PIN 35    
#define DS_PIN 4     // Pin untuk Sensor Suhu DS18B20

// LOGIKA TEGANGAN ESP32 (DIRECT CONNECT)
// Tanpa isolator, ESP32 membaca 0-3.3V = 0-4095
#define ESP_ADC_VREF 3300.0  // 3.3V
#define ESP_ADC_RES  4096.0  // 12-bit

OneWire ow(DS_PIN);
DallasTemperature objDS(&ow);

DFRobot_PH ph;
DFRobot_EC ec;

float voltagePH, phValue;
float voltageEC, ecValue;
float temperature = 25.0; // Nilai ini akan ditimpa oleh suhu asli DS18B20

void setup() {
  Serial.begin(115200);

  // Inisialisasi EEPROM
  // Library DFRobot biasanya otomatis memakai slot awal, 
  // kita siapkan 64 byte untuk menampung keduanya.
  EEPROM.begin(64);

  ph.begin();
  ec.begin();
  
  objDS.begin();
  objDS.setWaitForConversion(false); // Mode Non-Blocking agar pengetikan Serial tidak ngelag
  
  Serial.println("============================================");
  Serial.println("   SISTEM MONITORING SIAP (PH & EC)    ");
  Serial.println("   Ketik perintah untuk kalibrasi:          ");
  Serial.println("   pH: enterph -> calph -> exitph           ");
  Serial.println("   EC: enterec -> calec -> exitec           ");
  Serial.println("============================================");
}

// ==========================================
// FILTER DIGITAL: Oversampling & Median
// ==========================================
float getSmoothADC(int pin) {
  const int SAMPLES = 30;
  float readings[SAMPLES];
  
  for (int i = 0; i < SAMPLES; i++) {
    readings[i] = analogRead(pin);
    delayMicroseconds(100); 
  }
  
  for (int i = 0; i < SAMPLES - 1; i++) {
    for (int j = i + 1; j < SAMPLES; j++) {
      if (readings[i] > readings[j]) {float temp = readings[i]; readings[i] = readings[j]; readings[j] = temp;}
    }
  }
  
  float total = 0;
  for (int i = 10; i < 20; i++) total += readings[i];
  return total / 10.0f;
}

void loop() {
  static unsigned long timepoint = millis();
  if(millis() - timepoint > 1000U) {
    timepoint = millis();
    
    // 0. Baca Sensor Suhu Asli (DS18B20)
    objDS.requestTemperatures();
    float t_real = objDS.getTempCByIndex(0);
    // Masukkan suhu ke variabel utama jika angkanya masuk akal
    if (t_real != DEVICE_DISCONNECTED_C) {
      temperature = t_real;
    }
    
    // 1. Baca Sensor pH
    int adcPH = analogRead(PH_PIN);
    voltagePH = (float)adcPH / ESP_ADC_RES * ESP_ADC_VREF;
    phValue = ph.readPH(voltagePH, temperature);
    
    // 2. Baca Sensor EC
    int adcEC = analogRead(EC_PIN);
    voltageEC = ((float)adcEC / ESP_ADC_RES * ESP_ADC_VREF) * 1.4545;
    ecValue = ec.readEC(voltageEC, temperature);
    
    // 3. Tampilkan Data
    Serial.print("Suhu: "); Serial.print(temperature, 1); Serial.println(" C");
    Serial.print("pH Volt: "); Serial.print(voltagePH, 0); 
    Serial.print(" | pH: "); Serial.println(phValue, 2);
    
    Serial.print("EC Volt: "); Serial.print(voltageEC, 0); 
    Serial.print(" | EC: "); Serial.print(ecValue, 2); Serial.println(" ms/cm");
    Serial.println("----------------------------------------------");
  }

  // --- B. FUNGSI KALIBRASI (WAJIB JALAN TERUS) ---
  // Diletakkan di LUAR if(millis) agar selalu standby menerima ketikan.
  ph.calibration(voltagePH, temperature);
  ec.calibration(voltageEC, temperature);
}