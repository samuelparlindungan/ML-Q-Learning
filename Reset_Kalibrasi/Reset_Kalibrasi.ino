#include <EEPROM.h>

void setup() {
  Serial.begin(115200);
  EEPROM.begin(64);

  // Isi semua slot dengan 0xFF (nilai default/blank flash)
  for (int i = 0; i < 64; i++) {
    EEPROM.write(i, 0xFF);
  }

  bool ok = EEPROM.commit();
  Serial.println(ok ? "EEPROM berhasil direset!" : "EEPROM GAGAL direset!");
}

void loop() {}