/*
 * KODE KALIBRASI EC METER KHUSUS ESP32 (Direct Connect 3.3V)
 * 
 * Hardware Setup:
 * 1. Sensor EC terhubung langsung ke Shield/ESP32 (Tanpa Isolator).
 * 2. Jumper Voltage pada Shield HARUS di posisi 3.3V.
 * 3. Gunakan Pin ADC yang aman (Disarankan GPIO 35, 34, atau 36/VP).
 * 
 * Langkah Kalibrasi di Serial Monitor:
 * 1. Celup probe ke larutan 12.88ms/cm.
 * 2. Ketik: ENTEREC
 * 3. Ketik: CALEC
 * 4. Tunggu sampai muncul "Successful".
 * 5. Ketik: EXITEC (Wajib untuk menyimpan).
 */

#include "DFRobot_EC.h"
#include <EEPROM.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// --- KONFIGURASI PIN ---
// Ganti angka 34 sesuai pin yang Anda gunakan.
// Disarankan gunakan pin ADC1 (GPIO 32, 33, 34, 35, 36, 39) agar tidak konflik dengan Wi-Fi.
#define EC_PIN 35
#define DS_PIN 4

float voltage, ecValue, temperature = 25.0;
DFRobot_EC ec;
OneWire ow(DS_PIN);
DallasTemperature objDS(&ow);

void setup() {
  Serial.begin(115200); // Pastikan baudrate Serial Monitor sama dengan ini
  
  // Inisialisasi EEPROM khusus ESP32 (Alokasi 32 byte untuk data kalibrasi)
  EEPROM.begin(32); 
  
  ec.begin();
  
  objDS.begin();
  objDS.setWaitForConversion(false);
  Serial.println("SIAP UNTUK KALIBRASI");
  Serial.println("Pastikan jumper shield di 3.3V");
  Serial.println("Langkah: ENTEREC -> CALEC -> EXITEC");
}

void loop() {
  static unsigned long timepoint = millis();
  
  if(millis() - timepoint > 1000U) { // Update setiap 1 detik
    timepoint = millis();

    // BACA SUHU REAL-TIME DS18B20
    objDS.requestTemperatures();
    float t_real = objDS.getTempCByIndex(0);
    if (t_real != DEVICE_DISCONNECTED_C) {
      temperature = t_real;
    }
    
    // --- RUMUS TEGANGAN KHUSUS ESP32 (Jumper 3.3V) ---
    // analogRead(EC_PIN): Membaca nilai mentah (0 - 4095)
    // 4096.0: Resolusi ADC ESP32 (12-bit)
    // 3300.0: Tegangan referensi (3.3V dalam milivolt)
    
    voltage = analogRead(EC_PIN) / 4096.0 * 3300.0; 
    
    // Konversi tegangan ke nilai EC
    ecValue = ec.readEC(voltage, temperature); 
    
    Serial.print("Suhu:"); Serial.print(temperature, 1); Serial.print("C | ");
    Serial.print("Voltage:"); Serial.print(voltage); Serial.print("mV | ");
    Serial.print("EC:"); Serial.print(ecValue, 2); Serial.println(" ms/cm");
  }
  
  // Fungsi ini wajib ada di loop untuk membaca perintah Serial (ENTEREC, CALEC, EXITEC)
  ec.calibration(voltage, temperature); 
}