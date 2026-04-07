# Q-Learning untuk Kontrol pH dan EC Hidroponik (B600 Samuel & Josh)

Implementasi sistem kendali cerdas berbasis **Reinforcement Learning (Q-Learning)** untuk stabilitas pH dan EC pada tandon hidroponik 15 Liter. Proyek ini mengintegrasikan AI di Raspberry Pi dengan sensor/aktuator di ESP32 melalui protokol MQTT.

---

## 🚀 Fitur Baru: Autonomous Deployment (Update 2026)

Sistem telah ditingkatkan dari sekadar simulasi menjadi unit kontrol fisik mandiri yang siap untuk **Disturbance Test (Uji Gangguan)** Bab 4.

### ✅ **Auto-Control & Logging (`main_auto_control.py`)**
Script utama yang berjalan di Raspberry Pi untuk mengelola loop tertutup secara otonom:
- **Event-Driven:** Bereaksi langsung terhadap data dari `hidroponik/sensor`.
- **Auto-Logger:** Secara otomatis mencatat transisi $S_t \rightarrow Action \rightarrow S_{t+1}$ ke `output/data_transisi_otomatis.csv`.
- **Max Q-Value Tracking:** Mencatat nilai keyakinan agen di setiap langkah untuk analisis kualitas kebijakan AI di Bab 4.
- **Smart Homogenization:** Menunda observasi berikutnya selama 3 menit setelah aksi (termasuk IDLE) untuk memastikan larutan tercampur rata.

### ✅ **Safety & Reliability**
- **Sensor Anomaly Filter:** Menolak data jika pH < 0/>14 atau EC > 5000 (mencegah malfungsi pompa jika kabel lepas).
- **MQTT Reliability:** Menggunakan mekanisme acknowledgment `"DONE"` dari ESP32 sebelum memulai fase homogenisasi.

---

## 📁 Struktur Proyek (Terintegrasi)

```text
.
├── main_auto_control.py      # UNIT KONTROL OTONOM (Deploy di RPi)
├── main_training.py          # Script pelatihan agen (1500 Episode)
├── env_ph_ec.py              # Lingkungan simulasi (25 states, 9 actions)
├── qlearning_agent.py        # Logika Q-Learning (Adaptive Learning)
├── ESP_Sensor.ino            # Firmware Sensor (Node Publisher)
├── ESP32_Aktuator_Bypass.ino # Firmware Pompa (Node Subscriber)
├── konteks.md                # Master Context untuk kelanjutan proyek
├── output/                   # Hasil & Data Eksperimen
│   ├── policy.json           # "Otak" AI yang digunakan saat deploy
│   ├── data_transisi_otomatis.csv # LOG UTAMA UNTUK BAB 4
│   └── Q_table.npy           # Matriks Q hasil training
└── visualize.py              # Script visualisasi data training
```

---

## 🎯 Desain Sistem (Sesuai Metodologi B600)

### 1. State Space (25 States)
Didiskritisasi menjadi 5 level pH × 5 level EC.
- **Target Optimal**: State 13 (pH: 5.8 - 6.2, EC: 1100 - 1300 µS/cm).

### 2. Action Space (9 Actions)
| ID | Nama Aksi | Aktuator | Durasi |
|:---:|---|---|---|
| **0** | **IDLE** | - | - |
| **1-2** | **pH Up** | Pompa pH Up | Short / Long |
| **3-4** | **pH Down** | Pompa pH Down | Short / Long |
| **5-6** | **Nutrisi** | Pompa A & B | Short / Long |
| **7-8** | **Air Baku** | Pompa Air | Short / Long |

### 3. Reward Function (Zone-Based)
Agen didorong menuju target dengan insentif:
- **Target met**: +50
- **Sub-Optimal**: +10
- **Kritis**: -80
- **Kritis Ekstrem**: -120

---

## 🛠 Panduan Penggunaan Lapangan

### 1. Tahap Persiapan
1. Pastikan Broker MQTT (Mosquitto) menyala di Raspberry Pi (`192.168.100.10`).
2. Nyalakan ESP_Sensor dan ESP32_Aktuator.
3. Pastikan `policy.json` hasil training terbaru ada di folder `output/`.

### 2. Menjalankan Kontrol AI
Di terminal Raspberry Pi, jalankan:
```bash
python main_auto_control.py
```
Agen akan mulai memantau tandon dan mengeksekusi aksi otomatis. Semua data transisi akan masuk ke `output/data_transisi_otomatis.csv` untuk bahan penulisan **Bab 4 Skripsi**.

---

## 📚 Kontributor
- **Samuel P.** (B600: Implementasi Q-Learning & Kontrol Stabilitas)
- **Josh Delon** (B600: IoT Monitoring & Visualisasi Data Grafana)

**Prodi Teknik Elektro - Institut Teknologi Del (2025)**
