#include <Arduino.h>
#include <EEPROM.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "DFRobot_PH.h"
#include "DFRobot_EC.h"

// ==========================================
// 1. PIN & KONFIGURASI
// ==========================================
#define PH_PIN 34      // Pin Analog pH
#define EC_PIN 35      // Pin Analog EC
#define DS_PIN 4       // Pin Digital DS18B20
#define VREF 3300.0    // Tegangan Referensi ESP32 (3.3V)
#define ADCRES 4096.0  // Resolusi ADC ESP32 (12-bit)

// ==========================================
// 2. OBJEK & VARIABEL
// ==========================================
OneWire oneWire(DS_PIN);
DallasTemperature sensors(&oneWire);
DFRobot_PH ph;
DFRobot_EC ec;

float voltagePH, voltageEC;
float phValue, ecValue, temperature = 25.0;

// ==========================================
// 3. SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Inisialisasi Memori untuk Simpan Kalibrasi
  EEPROM.begin(64);
  
  // Inisialisasi Sensor
  sensors.begin();
  ph.begin();
  ec.begin();
  
  Serial.println("\n============================================");
  Serial.println("   SENSOR TEST: PH + EC + DS18B20 (ESP32)  ");
  Serial.println("   Metode: DFRobot Official + Stable Filter ");
  Serial.println("============================================");
  Serial.println("Ketik 'ENTERPH'/'ENTEREC' untuk kalibrasi.");
}

// ==========================================
// 4. LOOP
// ==========================================
void loop() {
  static unsigned long timePoint = millis();
  
  if (millis() - timePoint > 1000U) { // Update tiap 1 detik
    timePoint = millis();
    
    // --- LANGKAH 1: BACA SUHU AKTUAL (DS18B20) ---
    sensors.requestTemperatures();
    float tempReading = sensors.getTempCByIndex(0);
    if (tempReading != DEVICE_DISCONNECTED_C) {
      temperature = tempReading;
    }

    // --- LANGKAH 2: BACA TEGANGAN (FILTERING 40 SAMPEL) ---
    long totalAdcPH = 0;
    long totalAdcEC = 0;
    for (int i = 0; i < 40; i++) {
        totalAdcPH += analogRead(PH_PIN);
        totalAdcEC += analogRead(EC_PIN);
        delay(2);
    }
    
    // Konversi ADC ke miliVolt (mV) 
    // 1.4545f = Kompensasi Divider 1k/2.2k (Fisik)
    voltageEC = ((float)(totalAdcEC / 40) / ADCRES * VREF) * 1.4545f; 
    
    // Perhitungan pH (Tanpa Divider)
    voltagePH = (float)(totalAdcPH / 40) / ADCRES * VREF;

    // --- LANGKAH 3: HITUNG NILAI PH & EC (KOMPENSASI SUHU) ---
    phValue = ph.readPH(voltagePH, temperature);
    ecValue = ec.readEC(voltageEC, temperature); 

    // --- LANGKAH 4: OUTPUT SERIAL MONITOR ---
    Serial.print("Suhu:");
    Serial.print(temperature, 1);
    Serial.print("C | pH:");
    Serial.print(phValue, 2);
    Serial.print(" ("); Serial.print(voltagePH, 0); Serial.print("mV)");
    Serial.print(" | EC:");
    Serial.print(ecValue * 1000.0, 0); 
    Serial.print("uS/cm ("); Serial.print(voltageEC, 0); Serial.print("mV)");
    Serial.println();
  }

  // --- LANGKAH 5: PROSES KALIBRASI (SERIAL COMMAND) ---
  // Kalibrasi pH: ENTERPH -> CALPH -> EXITPH
  // Kalibrasi EC: ENTEREC -> CALEC -> EXITEC
  ph.calibration(voltagePH, temperature);
  ec.calibration(voltageEC, temperature);
}
