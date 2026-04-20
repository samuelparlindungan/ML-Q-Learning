# Model Konteks: Sistem Kontrol Hidroponik AI
(Single Source of Truth untuk Integrasi Skripsi)

## 🎯 1. OBJEKTIF UTAMA
Mengotomatisasi kontrol nutrisi (EC) dan keasaman (pH) pada sistem hidroponik menggunakan algoritma **Reinforcement Learning (Q-Learning)** untuk mencapai kondisi ideal (pH 6.0, EC 1200 uS/cm).

## 🚀 2. ALUR KERJA (PIPELINE)
1. **Sensor (ESP32)**: Membaca pH, EC, Suhu, dan Volume Tandon. Mengirim data JSON ke broker MQTT.
2. **Logic Agent (RPi/PC)**: Python men-subscribe data sensor, mengubahnya menjadi **State (1-25)**.
3. **Keputusan (Inference)**: AI memilih aksi terbaik (Idle, pH Up/Down, Nutrisi, Air) berdasarkan **Policy**.
4. **Aktuator (ESP32)**: Menjalankan pompa peristaltik sesuai perintah AI selama durasi tertentu (Short/Long).

## 📊 3. PARAMETER TEKNIS
- **Tandon Utama**: 15 Liter (Box Industri).
- **Ph Up/Down & Nutrisi**: Tabung 1 Liter.
- **Ambang Batas (Threshold)**: 
  - pH: 5.8 - 6.2 (Optimal).
  - EC: 1100 - 1300 uS/cm (Optimal).
- **Training**: 1500 Episode, 40 Steps/Episode.

## 🛡️ 4. DOUBLE SAFETY INTERLOCK
- **Sensor-Side**: ESP Sensor mengirim peringatan jika level cairan kritis.
- **Actuator-Side**: ESP Aktuator memblokir aksi pompa jika terdeteksi tandon/tabung kosong (proteksi dry-running).

## ⚙️ 5. MODE OPERASI
- **Mode Kontrol**: Otomatis (AI) vs Manual (Maintenance CLI).
- **Versi Lingkungan**: 
  - `v1_teori`: Berbasis simulasi matematika.
  - `v2_dataset`: Berbasis data empiris dari tandon asli (Dataset Aktual).

## 📂 6. PETA WORKSPACE (FILE TREE)
```text
/ (Root)
│
├── Kalibrasi_pH/               # Tool Kalibrasi pH
├── Kalibrasi_EC/               # Tool Kalibrasi EC
├── Kombinasi_pH_EC/            # Kode Gabungan pH & EC
├── Sistem_Kontrol_AI/          # Folder Pusat Skrip AI (Python)
│   ├── env_ph_ec.py            # Environment Digital Twin
│   ├── qlearning_agent.py      # Logika Algoritma Q-Learning
│   ├── main_training.py        # Skrip Training Versi Terpilih
│   ├── main_auto_control.py    # Skrip Kontrol Otomatis
│   ├── visualize.py            # Visualisasi Progress Training
│   ├── buat_grafik.py          # Generator Grafik PNG untuk Skripsi
│   └── cek_nilai_q.py          # Export Q-Table ke Excel
│   ├── random_explorer_v1.py   # Automated Data Collector
│   └── kolektor_data_pro.py    # Manual Data Collector
│
├── output/                     # Hasil Training Berbasis Versi
│   ├── v1_teori/               # Arsip Hasil Training Simulasi
│   └── v2_dataset/             # Hasil Training berbasis Data Aktual
│
├── ESP_Sensor.ino              # Firmware Sensor Produksi
└── ESP32_Aktuator_Maintenance/ # Firmware Aktuator (Safety + Maintenance)
```

---
*Dibuat untuk memastikan integrasi lintas-hardware dan kebutuhan akademik Samuel & Josh tetap sinkron.*
