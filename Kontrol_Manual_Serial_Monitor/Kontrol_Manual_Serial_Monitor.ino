// ==========================================
// 1. PIN RELAY (Sesuai Konfigurasi Kamu)
// ==========================================
const int RELAY_PH_UP = 14;    // Pompa 1
const int RELAY_PH_DOWN = 27;  // Pompa 2
const int RELAY_NUT_A = 26;    // Pompa 3
const int RELAY_NUT_B = 25;    // Pompa 4
const int RELAY_AIR = 33;      // Pompa 5

void setup() {
  Serial.begin(115200);

  // Inisialisasi Pin
  pinMode(RELAY_PH_UP, OUTPUT);
  pinMode(RELAY_PH_DOWN, OUTPUT);
  pinMode(RELAY_NUT_A, OUTPUT);
  pinMode(RELAY_NUT_B, OUTPUT);
  pinMode(RELAY_AIR, OUTPUT);

  // Pastikan semua OFF di awal (Active Low: HIGH = OFF)
  digitalWrite(RELAY_PH_UP, HIGH);
  digitalWrite(RELAY_PH_DOWN, HIGH);
  digitalWrite(RELAY_NUT_A, HIGH);
  digitalWrite(RELAY_NUT_B, HIGH);
  digitalWrite(RELAY_AIR, HIGH);

  Serial.println("==========================================");
  Serial.println("      KONTROL MANUAL POMPA HIDROPONIK     ");
  Serial.println("==========================================");
  Serial.println("Format ketik: [Nomor_Pompa] [Durasi_Detik]");
  Serial.println("Contoh: '1 5' (pH Up nyala 5 detik)");
  Serial.println("------------------------------------------");
  Serial.println("Daftar Pompa:");
  Serial.println("1: pH UP");
  Serial.println("2: pH DOWN");
  Serial.println("3: NUTRISI A");
  Serial.println("4: NUTRISI B");
  Serial.println("5: AIR BAKU");
  Serial.println("------------------------------------------");
}

void loop() {
  // Cek jika ada input masuk di Serial Monitor
  if (Serial.available() > 0) {

    // Membaca nomor pompa (angka pertama)
    int nomor = Serial.parseInt();
    // Membaca durasi dalam detik (angka kedua)
    int durasiDetik = Serial.parseInt();

    // Membersihkan sisa karakter (seperti \n atau \r)
    while (Serial.available() > 0) Serial.read();

    // Validasi input
    if (nomor >= 1 && nomor <= 5 && durasiDetik > 0) {
      eksekusiPompa(nomor, durasiDetik);
    } else if (nomor != 0) {
      Serial.println("⚠️ Input tidak valid! Gunakan format: [1-5] [durasi]");
    }
  }
}

void eksekusiPompa(int nomor, int detik) {
  int pinTarget;
  String namaPompa;
  unsigned long ms = detik * 1000;  // Konversi ke milidetik

  // Pemilihan Pin berdasarkan nomor
  switch (nomor) {
    case 1:
      pinTarget = RELAY_PH_UP;
      namaPompa = "pH UP";
      break;
    case 2:
      pinTarget = RELAY_PH_DOWN;
      namaPompa = "pH DOWN";
      break;
    case 3:
      pinTarget = RELAY_NUT_A;
      namaPompa = "NUTRISI A";
      break;
    case 4:
      pinTarget = RELAY_NUT_B;
      namaPompa = "NUTRISI B";
      break;
    case 5:
      pinTarget = RELAY_AIR;
      namaPompa = "AIR BAKU";
      break;
    default: return;
  }

  // Proses Eksekusi
  Serial.print(">> Menyalakan ");
  Serial.print(namaPompa);
  Serial.print(" selama ");
  Serial.print(detik);
  Serial.println(" detik...");

  digitalWrite(pinTarget, LOW);   // ON (Active Low)
  delay(ms);                      // Tunggu
  digitalWrite(pinTarget, HIGH);  // OFF

  Serial.println(">> Selesai.");
  Serial.println("------------------------------------------");
}