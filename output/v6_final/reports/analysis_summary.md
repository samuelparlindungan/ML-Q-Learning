# Analisis Hasil Pelatihan Reinforcement Learning (v6_final)

## 1. Konvergensi Sistem
- **Reward Awal (Rata-rata 500 ep):** -328.14
- **Reward Akhir (Rata-rata 500 ep):** 969.50
- **Interpretasi:** Sistem menunjukkan peningkatan reward yang signifikan, mengindikasikan keberhasilan Reward Shaping.

## 2. Distribusi Kunjungan State
Top 5 State paling sering dikunjungi:
- **State 15**: 179611 kunjungan
- **State 10**: 101235 kunjungan
- **State 13**: 52410 kunjungan
- **State 20**: 44208 kunjungan
- **State 14**: 26251 kunjungan

### Analisis State:
- **State 13 (Target)** dikunjungi sebanyak 52410 kali.
- **State Kritis Ekstrem** (1, 5, 21, 25) memiliki total kunjungan gabungan 11697 kali, menunjukkan agen sangat berhati-hati.

## 3. Analisis Kebijakan (Policy)
Berikut ringkasan aksi untuk beberapa kondisi kritis:
- **pH Sangat Rendah (State 1-5)**: Aksi dominan adalah 2 (lihat mapping).
- **EC Sangat Tinggi (State 5, 10, 15, 20, 25)**: Agen memprioritaskan dilusi.

