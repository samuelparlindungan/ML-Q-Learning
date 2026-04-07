# RINGKASAN KONTEKS PROYEK (FOR AI CONTINUATION)

Dokumen ini berfungsi sebagai "Ingatan Permanen" untuk asisten AI berikutnya jika terjadi pergantian akun atau sesi. Ini merangkum seluruh arsitektur, keputusan desain, dan status terakhir proyek Tugas Akhir Samuel & Josh.

---

## 1. TUJUAN PROYEK
Otomatisasi kendali pH dan EC pada sistem hidroponik menggunakan **Reinforcement Learning (Q-Learning)** dengan arsitektur **Edge Computing** (Raspberry Pi + ESP32).

**Kolaborasi Tim:**
- **Samuel (B600 - Penulis):** Fokus pada Algoritma AI, Policy Training, dan Logic Controller (Raspberry Pi).
- **Josh (B600 - Partner):** Fokus pada IoT Monitoring, Wiring Sensor, Data Visualization, dan Dashboard (Grafana).

---

## 2. ARSITEKTUR TEKNIS
- **Pusat Komputasi (Agent):** Raspberry Pi 4 (Menjalankan Python).
- **Node Sensor (Publisher):** ESP32 (Membaca pH, EC, Suhu, Ultrasonik, Flow). Topic: `hidroponik/sensor`.
- **Node Aktuator (Subscriber):** ESP32 (Mengendalikan 5 Pompa Peristaltik). Topic: `hidroponik/action`.
- **Protokol:** MQTT (Broker di RPi IP: `192.168.100.10`).
- **Database & Visualisasi:** Telegraf -> InfluxDB -> Grafana.

---

## 3. DESAIN Q-LEARNING (CORE AI)
- **State Space (25 State):** Diskritisasi pH (5 Level) x EC (5 Level).
- **Action Space (9 Action):**
    - `0`: IDLE (Diam)
    - `1-2`: pH Up (Short/Long)
    - `3-4`: pH Down (Short/Long)
    - `5-6`: Nutrisi A&B (Short/Long)
    - `7-8`: Air Baku (Short/Long)
- **Training:** Menggunakan `main_training.py` dengan 1500 episode (sesuai draf B600). Output: `policy.json`.
- **Inference:** `main_auto_control.py` membaca `policy.json` untuk menentukan aksi tanpa perlu training ulang di RPi.

---

## 4. STATUS TERAKHIR & FITUR SPESIFIK (CRITICAL)
File **`main_auto_control.py`** telah dimodifikasi secara mendalam dengan fitur:
1.  **Auto-Logging CSV (`output/data_transisi_otomatis.csv`)**: Mencatat `St`, `Action`, `St+1`, `Delta`, dan `Max_Q_Value`.
2.  **Consistent Homogenization**: Aksi 0 (IDLE) sekarang juga memicu delay 3 menit agar data CSV konsisten dengan data manual untuk perbandingan Bab 4.
3.  **Safety Interlock**: Menolak aksi jika sensor membaca anomali (pH < 0 atau > 14, EC < 0 atau > 5000) untuk mencegah kerusakan tandon jika kabel lepas.
4.  **MQTT Protocol**: Mengirim payload angka murni (`0`-`8`) sesuai protokol `ESP32_Aktuator_Bypass.ino`.

---

## 5. RENCANA PENGUJIAN BAB 4 (HASUL & PEMBAHASAN)
- **Disturbance Test:** Tandon 15L kondisi optimal -> Kurangi 1L s/d 5L -> Ganti air baku -> Amati kecepatan pemulihan AI.
- **Comparison:** Membandingkan efisiensi langkah dan *settling time* antara `data_transisi_manual.csv` vs `data_transisi_otomatis.csv`.
- **Metadata Log:** Memastikan kolom `Max_Q_Value` digunakan untuk membuktikan keputusan berbasis AI di dalam naskah paper/sidang.

---

## 6. DAFTAR FILE UTAMA
- `env_ph_ec.py`: Lingkungan simulasi untuk training.
- `qlearning_agent.py`: Logika algoritma agen (Learning Rate, Epsilon).
- `main_auto_control.py`: Script utama yang harus *running* di Raspberry Pi.
- `ESP_Sensor.ino`: Firmware monitoring (Josh).
- `ESP32_Aktuator_Bypass.ino`: Firmware eksekusi pompa.
- `policy.json`: "Otak" hasil training yang digunakan saat ini. 

---
*Dokumen ini dibuat untuk memastikan asisten AI berikutnya tidak kehilangan konteks mengenai integrasi lintas-hardware dan kebutuhan spesifik skripsi Samuel.*
