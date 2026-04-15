#include "DFRobot_PH.h"
#include <EEPROM.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define PH_PIN 34          // Pin Analog ESP32
#define DS_PIN 4
#define VREF 3300          // Tegangan referensi ESP32 (3300mV)
#define ADC_RES 4096.0     // Resolusi ADC ESP32 (12-bit)

float voltage, phValue, temperature = 25.0;
DFRobot_PH ph;
OneWire ow(DS_PIN);
DallasTemperature objDS(&ow);

void setup() {
    Serial.begin(115200);  
    
    // PENYESUAIAN 1: ESP32 butuh inisialisasi EEPROM sebelum ph.begin()
    EEPROM.begin(32); 
    
    ph.begin();

    objDS.begin();
    objDS.setWaitForConversion(false);
}

void loop() {
    static unsigned long timepoint = millis();
    if(millis() - timepoint > 1000U) {
        timepoint = millis();
        
        // BACA SUHU REAL-TIME DS18B20
        objDS.requestTemperatures();
        float t_real = objDS.getTempCByIndex(0);
        if (t_real != DEVICE_DISCONNECTED_C) {
            temperature = t_real;
        }
        
        // PENYESUAIAN 2: Rumus perhitungan Voltage untuk ESP32
        // Kalikan 1.4545 untuk mencairkan efek Voltage Divider 1K & 2.2K
        voltage = ((float)analogRead(PH_PIN) / ADC_RES * VREF) * 1.4545;
        
        phValue = ph.readPH(voltage, temperature);
        
        Serial.print("Suhu:"); Serial.print(temperature, 1); Serial.print("C | ");
        Serial.print("Volt:"); Serial.print(voltage, 1); Serial.print("mV | ");
        Serial.print("pH:"); Serial.println(phValue, 2);
    }
    
    // Tetap gunakan fungsi ini untuk kalibrasi via Serial Monitor
    ph.calibration(voltage, temperature); 
}