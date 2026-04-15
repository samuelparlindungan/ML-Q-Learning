/*
 * KODE KALIBRASI ULTRASONIK (TABUNG T1-T5)
 * Digunakan untuk mencari nilai T_OFFSET dan T_LUAS secara akurat.
 */

// ==========================================
// KONFIGURASI PIN (SESUAIKAN DENGAN ESP32 ANDA)
// ==========================================
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

// Variabel penampung hasil kalibrasi sementara
float current_OFFSET = 0;
float current_LUAS = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Inisialisasi Pin Ultrasonik
  int trigPins[] = {T1_TRIG, T2_TRIG, T3_TRIG, T4_TRIG, T5_TRIG, BX_TRIG};
  int echoPins[] = {T1_ECHO, T2_ECHO, T3_ECHO, T4_ECHO, T5_ECHO, BX_ECHO};
  for (int i = 0; i < 6; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }

  Serial.println("\n=== KALIBRASI ULTRASONIK STANDALONE ===");
  Serial.println("Ketik 'kaltabung' untuk memulai asisten kalibrasi.");
  Serial.println("Ketik 'ping' untuk cek jarak mentah semua sensor.");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toLowerCase();

    if (cmd == "kaltabung") {
      jalankanKalibrasi();
    } else if (cmd == "ping") {
      cekSemuaSensor();
    }
  }
}

// ==========================================
// FUNGSI UTAMA KALIBRASI
// ==========================================
void jalankanKalibrasi() {
  Serial.println("\n[PILIH TABUNG]");
  Serial.println("Masukkan nomor tabung yang ingin dikalibrasi (1-5):");
  while (!Serial.available()) delay(100);
  int choice = Serial.parseInt();
  while (Serial.available()) Serial.read(); // Clear buffer

  if (choice < 1 || choice > 5) {
    Serial.println("Pilihan tidak valid!");
    return;
  }

  int trigArr[] = {T1_TRIG, T2_TRIG, T3_TRIG, T4_TRIG, T5_TRIG};
  int echoArr[] = {T1_ECHO, T2_ECHO, T3_ECHO, T4_ECHO, T5_ECHO};
  int tTrig = trigArr[choice - 1];
  int tEcho = echoArr[choice - 1];

  Serial.printf("\n--- Memulai Kalibrasi Tabung T%d ---\n", choice);

  // LANGKAH 1: KOSONG
  Serial.println("[1] KOSONGKAN tabung sepenuhnya, lalu tekan ENTER...");
  tungguEnter();
  float jarakKosong = ambilMedianJarak(tTrig, tEcho);
  if (jarakKosong < 0) { Serial.println("Error Baca Sensor!"); return; }
  Serial.printf("Jarak Kosong (T_OFFSET): %.2f cm\n", jarakKosong);

  // LANGKAH 2: ISI 500mL
  Serial.println("\n[2] MASUKKAN tepat 500 mL air, lalu tekan ENTER...");
  tungguEnter();
  float jarakIsi = ambilMedianJarak(tTrig, tEcho);
  if (jarakIsi < 0) { Serial.println("Error Baca Sensor!"); return; }
  Serial.printf("Jarak saat 500mL: %.2f cm\n", jarakIsi);

  // LANGKAH 3: HITUNG
  float tinggiAir = jarakKosong - jarakIsi;
  if (tinggiAir <= 0.1) {
    Serial.println("Gagal: Tidak ada perubahan tinggi air!");
    return;
  }
  float luasArea = 500.0 / tinggiAir;

  Serial.println("\n=== HASIL KALIBRASI ===");
  Serial.printf("Tinggi Air 500mL : %.2f cm\n", tinggiAir);
  Serial.printf("T_OFFSET (Baru)  : %.2f cm\n", jarakKosong);
  Serial.printf("T_LUAS (Baru)    : %.2f cm2\n", luasArea);
  Serial.println("=======================");

  // LANGKAH 4: VERIFIKASI 300mL
  Serial.println("\n[3] VERIFIKASI: Ubah isi air ke 300 mL, lalu tekan ENTER...");
  tungguEnter();
  float jarakVer = ambilMedianJarak(tTrig, tEcho);
  float volVer = (jarakKosong - jarakVer) * luasArea;
  
  Serial.printf("Volume Terbaca: %.1f mL (Target: 300 mL)\n", volVer);
  Serial.printf("Selisih: %.1f mL\n", abs(volVer - 300.0));
  
  if (abs(volVer - 300.0) <= 15.0) {
    Serial.println("✅ SUKSES! Nilai sudah akurat.");
  } else {
    Serial.println("❌ ERROR > 5%! Ulangi kalibrasi dengan lebih teliti.");
  }
}

// ==========================================
// HELPER FUNCTIONS
// ==========================================

void tungguEnter() {
  while (Serial.available()) Serial.read();
  while (!Serial.available()) delay(100);
  while (Serial.available()) Serial.read();
}

float ambilMedianJarak(int trig, int echo) {
  const int N = 15;
  float s[N];
  int count = 0;
  for (int i = 0; i < N; i++) {
    digitalWrite(trig, LOW); delayMicroseconds(2);
    digitalWrite(trig, HIGH); delayMicroseconds(10);
    digitalWrite(trig, LOW);
    long duration = pulseIn(echo, HIGH, 35000);
    float d = duration * 0.0343 / 2.0;
    if (d > 0.5 && d < 400) s[count++] = d;
    delay(40);
  }
  if (count < 5) return -1;
  
  // Sort
  for (int i = 0; i < count - 1; i++) {
    for (int j = i + 1; j < count; j++) {
      if (s[j] < s[i]) { float t = s[i]; s[i] = s[j]; s[j] = t; }
    }
  }
  return s[count / 2];
}

void cekSemuaSensor() {
  int trigArr[] = {T1_TRIG, T2_TRIG, T3_TRIG, T4_TRIG, T5_TRIG, BX_TRIG};
  int echoArr[] = {T1_ECHO, T2_ECHO, T3_ECHO, T4_ECHO, T5_ECHO, BX_ECHO};
  String names[] = {"T1", "T2", "T3", "T4", "T5", "BOX"};
  
  Serial.println("\n--- Jarak Mentah (cm) ---");
  for (int i = 0; i < 6; i++) {
    float d = ambilMedianJarak(trigArr[i], echoArr[i]);
    Serial.printf("%s: %.2f cm | ", names[i].c_str(), d);
    if (i == 2) Serial.println();
  }
  Serial.println("\n-------------------------");
}
