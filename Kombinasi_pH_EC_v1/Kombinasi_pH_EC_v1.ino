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

  EEPROM.begin(64);
  ph.begin();
  ec.begin();
  
  objDS.begin();
  objDS.setWaitForConversion(false); 
  
  Serial.println("============================================");
  Serial.println("   SISTEM MONITORING SIAP (PH & EC)    ");
  Serial.println("   Ketik perintah untuk kalibrasi:          ");
  Serial.println("   pH: enterph -> calph -> exitph           ");
  Serial.println("   EC: enterec -> calec -> exitec           ");
  Serial.println("============================================");
}

void loop() {
  static unsigned long timepoint = millis();
  if(millis() - timepoint > 1000U) {
    timepoint = millis();
    
    // 0. Baca Suhu untuk kompensasi
    objDS.requestTemperatures();
    float t_real = objDS.getTempCByIndex(0);
    if (t_real != DEVICE_DISCONNECTED_C) temperature = t_real;
    
    // ── 1. Baca Sensor pH & EC dengan 40 Sampel (Sama dengan ESP32_Sensor) ──
    long totalAdcPH = 0;
    long totalAdcEC = 0;
    for(int i = 0; i < 40; i++) {
        totalAdcPH += analogRead(PH_PIN);
        totalAdcEC += analogRead(EC_PIN);
        delay(2); // Jeda 2 milidetik per sampel untuk kestabilan ADC
    }
    int avgAdcPH = totalAdcPH / 40;
    int avgAdcEC = totalAdcEC / 40;

    // pH menggunakan pembacaan murni (Direct)
    voltagePH = (float)avgAdcPH / ESP_ADC_RES * ESP_ADC_VREF;
    phValue = ph.readPH(voltagePH, temperature);
    
    // Kalikan 1.4545 untuk mencairkan efek Voltage Divider pada EC
    voltageEC = ((float)avgAdcEC / ESP_ADC_RES * ESP_ADC_VREF) * 1.4545f;
    ecValue = ec.readEC(voltageEC, temperature);
    
    // 3. Tampilkan Data
    Serial.print("Suhu: "); Serial.print(temperature, 1); Serial.println(" C");
    Serial.print("pH Volt: "); Serial.print(voltagePH, 0); 
    Serial.print(" | pH: "); Serial.println(phValue, 2);
    
    Serial.print("EC Volt: "); Serial.print(voltageEC, 0); 
    Serial.print(" | EC: "); Serial.print(ecValue, 2); Serial.println(" ms/cm");
    Serial.println("----------------------------------------------");
  }

  // --- B. FUNGSI KALIBRASI ---
  ph.calibration(voltagePH, temperature);
  ec.calibration(voltageEC, temperature);
}