// ==========================================
// KONTROL MANUAL POMPA PARALEL (NON-BLOCKING)
// ==========================================
// Pin Relay (Active Low)
const int RELAY_PH_UP   = 14; 
const int RELAY_PH_DOWN = 27; 
const int RELAY_AIR     = 26; 
const int RELAY_NUT_A   = 25; 
const int RELAY_NUT_B   = 33; 

// Array untuk mempermudah akses (indeks 1-5)
// Urutan tetap: 1:PH_UP, 2:PH_DN, 3:NUT_A, 4:NUT_B, 5:AIR
const int PUMP_PINS[6] = {0, RELAY_PH_UP, RELAY_PH_DOWN, RELAY_NUT_A, RELAY_NUT_B, RELAY_AIR};
const String PUMP_NAMES[6] = {"", "pH UP", "pH DOWN", "NUTRISI A", "NUTRISI B", "AIR BAKU"};

// Variabel Timer (Millis)
unsigned long stopTime[6] = {0, 0, 0, 0, 0, 0};

void setup() {
  Serial.begin(115200);

  for (int i = 1; i <= 5; i++) {
    pinMode(PUMP_PINS[i], OUTPUT);
    digitalWrite(PUMP_PINS[i], HIGH); // OFF di awal
  }

  Serial.println("\n==========================================");
  Serial.println("   KONTROL MANUAL POMPA (MULTITASKING)    ");
  Serial.println("==========================================");
  Serial.println("Format: [Nomor_Pompa] [Durasi_Detik]");
  Serial.println("Contoh: '1 50' lalu '2 50' (Jalan Bareng)");
  Serial.println("Ketik '0' untuk mematikan SEMUA pompa.");
  Serial.println("------------------------------------------");
}

void loop() {
  // 1. CEK TIMER POMPA (Non-Blocking)
  unsigned long sekarang = millis();
  for (int i = 1; i <= 5; i++) {
    if (stopTime[i] > 0 && sekarang >= stopTime[i]) {
      digitalWrite(PUMP_PINS[i], HIGH); // Matikan (OFF)
      stopTime[i] = 0;                  // Reset timer
      Serial.printf(">> %s Selesai (Otomatis OFF)\n", PUMP_NAMES[i].c_str());
    }
  }

  // 2. CEK INPUT SERIAL
  if (Serial.available() > 0) {
    int nomor = Serial.parseInt();
    int durasi = Serial.parseInt();

    // Clear buffer
    while (Serial.available() > 0) Serial.read();

    if (nomor == 0) {
      stopSemua();
    } 
    else if (nomor >= 1 && nomor <= 5 && durasi > 0) {
      nyalakanPompa(nomor, durasi);
    } 
    else if (nomor != 0) {
      Serial.println("⚠️ Input salah! Gunakan: [1-5] [durasi]");
    }
  }
}

void nyalakanPompa(int nomor, int detik) {
  // Batasi durasi maksimal (misal 5 menit untuk pengamanan)
  if (detik > 300) detik = 300; 

  // Hitung waktu berhenti
  stopTime[nomor] = millis() + (unsigned long)detik * 1000;

  digitalWrite(PUMP_PINS[nomor], LOW); // ON (Active Low)

  Serial.printf(">> %s AKTIF selama %d detik\n", PUMP_NAMES[nomor].c_str(), detik);
}

void stopSemua() {
  Serial.println("!!! EMERGENCY STOP: SEMUA POMPA MATI !!!");
  for (int i = 1; i <= 5; i++) {
    digitalWrite(PUMP_PINS[i], HIGH);
    stopTime[i] = 0;
  }
}