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
- **Node Aktuator (ESP32)**: `ESP32_Aktuator_Bypass/ESP32_Aktuator_Bypass.ino`.
    - **Pin Relay (Active LOW)**: pH Up (14), pH Down (27), Air Baku (26), Nutrisi A (25), Nutrisi B (33).
    - **Fitur Kunci**: 
        - `smartDelay()`: Menangani jeda pompa tanpa memutus koneksi MQTT.
        - **Real-time Report**: Mengirim status `1` (ON) dan `0` (OFF) ke topik `hidroponik/aktuator`.
        - **Sinkronisasi**: Mengirim payload `"DONE"` ke `hidroponik/status` setelah aksi selesai.

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
1. **Auto-Logging CSV**: `output/data_transisi_otomatis.csv` mencatat `St`, `Action`, `St+1`, `Delta`, dan `Max_Q_Value`.
2. **Homogenisasi Konsisten**: Setiap aksi (termasuk IDLE) memicu jeda 3 menit agar data CSV konsisten untuk validasi Bab 4.
3. **Safety Interlock**: Filtrasi anomali sensor (pH 0-14, EC 0-5000) di sisi Python untuk mencegah pemompaan berlebih.
4. **Monitoring Pipeline**:
    - **Telegraf Config**: Menambahkan topik `hidroponik/aktuator` dan `json_string_fields = ["nama_pompa", "tampilan"]`.
    - **Visualisasi**: Field `tampilan` (e.g. "ON / 2.0s") digunakan untuk dashboard State Timeline di Grafana.

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
├── main_auto_control.py        # Controller Utama (Autonomous Mode)
├── qlearning_agent.py          # Implementasi Algoritma RL
├── env_ph_ec.py                # Environment Sensor Logic
├── telegraf.conf               # Konfigurasi Jembatan Data (MQTT-InfluxDB)
├── STABILITAS_Q_VALUE.md       # Catatan Tuning & Konvergensi AI
│
├── ESP32_Aktuator_Bypass/      # Firmware Aktuator (Pompa)
├── ESP_Sensor.ino              # Firmware Sensor (Monitoring)
│
├── output/                     # Hasil AI: policy.json, CSV Logs
└── Bimbingan/Dokumen/          # File Naskah Skripsi & Revisi (.docx, .pdf)
```

---
*Dibuat untuk memastikan integrasi lintas-hardware dan kebutuhan akademik Samuel & Josh tetap sinkron.*
