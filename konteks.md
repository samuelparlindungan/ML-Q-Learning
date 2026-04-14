# 📑 KONTEKS MASTER: SISTEM HIDROPONIK AI (SAMUEL & JOSH)

Dokumen ini berfungsi sebagai "Ingatan Permanen" dan "Single Source of Truth" untuk seluruh kemajuan proyek, arsitektur, dan kebutuhan penelitian Tugas Akhir. **DILARANG MENGHAPUS BAGIAN PENELITIAN.**

---

## 1. 🎯 IDENTITAS PROYEK & KOLABORASI (B600)
- **Tujuan**: Otomatisasi kendali pH dan EC pada sistem hidroponik menggunakan **Reinforcement Learning (Q-Learning)** dengan arsitektur **Edge Computing** (Raspberry Pi + ESP32).
- **Kolaborasi Tim**:
    - **Samuel (Penulis)**: Fokus pada Algoritma AI, Policy Training, dan Logic Controller (Raspberry Pi).
    - **Josh (Partner)**: Fokus pada IoT Monitoring, Wiring Sensor, Data Visualization, dan Dashboard (Grafana).

---

## 🏗️ 2. ARSITEKTUR TEKNIS & HARDWARE
- **Pusat Komputasi (Agent)**: Raspberry Pi 4 (Python 3). IP Broker: `192.168.100.10`.
- **Node Sensor (ESP32)**: `ESP_Sensor.ino`.
    - **Power Setup**: pH (3.3V Direct), EC (5V via Analog Isolator DFR0504 + Voltage Divider 1k/2.2k).
    - **Signal Logic**: EC menggunakan pengali `1.4545` (untuk netralisir resistor), pH tanpa pengali.
- **Node Aktuator (ESP32)**: `ESP32_Aktuator_Bypass/ESP32_Aktuator_Bypass.ino`.
    - **Pin Relay (Active LOW)**: pH Up (14), pH Down (27), Air Baku (26), Nutrisi A (25), Nutrisi B (33).
    - **Fitur Kunci**: 
        - `smartDelay()`: Menangani jeda pompa tanpa memutus koneksi MQTT.
        - **Real-time Report**: Mengirim status kelima pompa sekaligus dalam format JSON ke `hidroponik/aktuator`.

---

## 🧠 3. DESAIN Q-LEARNING (CORE AI)
- **State Space (25 State)**: Diskritisasi pH (5 Level) x EC (5 Level).
    - pH: `<5.5`, `<5.8`, `5.8-6.2`, `6.2-6.5`, `>6.5`.
    - EC: `<800`, `<1100`, `1100-1300`, `1300-1600`, `>1600`.
- **Action Space (9 Aksi)**: 0 (IDLE), 1-2 (pH Up S/L), 3-4 (pH Down S/L), 5-6 (Nutrisi S/L), 7-8 (Air S/L).
- **Training Strategy**: 1500 episode dengan **Dual Decay** (Adaptive Alpha & Epsilon) untuk stabilitas Q-Value (Lihat: `STABILITAS_Q_VALUE.md`).
- **Inference**: Menggunakan `policy.json` untuk pengambilan keputusan real-time.

---

## 📊 4. STATUS TERAKHIR & FITUR KRITIS (CRITICAL)
1. **Stabilisasi Sensor**: Implementasi `getSmoothADC` (Median Filter 30 sampel) pada pH dan EC untuk membuang noise Wi-Fi dan interferensi pulsa EC di air.
2. **Kompensasi Suhu Real-time**: Seluruh modul kalibrasi (`Kalibrasi_EC`, `Kalibrasi_pH`, `Kombinasi_pH_EC`) sudah terintegrasi dengan DS18B20 (Non-Blocking).
3. **Data Logging**: `output/data_transisi_otomatis.csv` mencatat `St`, `Action`, `St+1`, `Delta`, dan `Max_Q_Value`.
4. **Monitoring Pipeline**:
    - **Telegraf Config**: Mendukung multi-field JSON parsing untuk status aktuator serentak.
    - **Grafana**: Dashboard dikonfigurasi untuk menampilkan tren pH/EC yang sudah difilter (mulus).

---

## 📝 5. RENCANA PENGUJIAN & VALIDASI BAB 4
- **Disturbance Test**: Uji pemulihan AI saat volume tandon (15L) dikurangi atau air diganti (simulasi gangguan nyata).
- **Comparison Analysis**: Membandingkan efisiensi langkah antara `data_transisi_manual.csv` vs `data_transisi_otomatis.csv`.
- **Bukti Ilmiah**: Penggunaan kolom `Max_Q_Value` untuk membuktikan kemantapan kebijakan (policy) AI dalam naskah skripsi.

---

## 📂 6. PETA WORKSPACE (FILE TREE)
```text
/ (Root)
│
├── Kalibrasi_pH/               # Tool Kalibrasi pH (DS18B20 Real-time)
├── Kalibrasi_EC/               # Tool Kalibrasi EC (Multiplier 1.4545 + DS18B20)
├── Kombinasi_pH_EC/            # Kode Gabungan (Filter Median + Suhu Real-time)
├── ESP32_Aktuator_Bypass/      # Firmware Aktuator (Pompa + JSON Reporting)
├── ESP_Sensor.ino              # Firmware Produksi (DSP Filter + Async Suhu)
│
├── main_auto_control.py        # Controller Utama (Autonomous Mode)
├── qlearning_agent.py          # Implementasi Algoritma RL
├── env_ph_ec.py                # Environment Sensor Logic
├── telegraf.conf               # Konfigurasi Jembatan Data (MQTT-InfluxDB)
│
├── output/                     # Hasil AI: policy.json, CSV Logs
└── Bimbingan/Dokumen/          # File Naskah Skripsi & Revisi (.docx, .pdf)
```

---
*Dibuat untuk memastikan integrasi lintas-hardware dan kebutuhan akademik Samuel & Josh tetap sinkron.*
