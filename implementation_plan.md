# Rencana Sinkronisasi Simulasi dengan Data Tandon Asli

Tujuan: Memperbarui logika `env_ph_ec.py` agar nilai perubahan pH dan EC saat `step()` dipanggil mencerminkan hasil eksperimen nyata yang tercatat di CSV.

## User Review Required

> [!IMPORTANT]
> - **Aksi 7 & 8 (Air Baku)**: Di data Anda, Air Baku tidak menurunkan EC secara drastis (malah cenderung naik sangat sedikit). Apakah Anda ingin simulasi mengikuti data asli ini, atau tetap menggunakan logika teori (Air Baku menurunkan EC)?
> - **Kekuatan pH Up**: Data menunjukkan pH Up cukup lemah (+0.28). Saya akan menggunakan nilai ini agar AI terbiasa melakukan aksi berulang jika butuh kenaikan besar.

## Proposed Changes

### [Component] env_ph_ec.py

#### [MODIFY] [env_ph_ec.py](file:///d:/GitHub/Tes%20Antigravity+Opencode/env_ph_ec.py)

1. **Update `step()` function**:
   Mengganti nilai `delta_ph` dan `delta_ec` keras (placeholder) dengan angka hasil analisis:
   - Aksi 1: ph +0.07 | ec +25
   - Aksi 2: ph +0.28 | ec +28
   - Aksi 3: ph -0.12 | ec +36
   - Aksi 4: ph -0.41 | ec +10
   - Aksi 5: ph -0.03 | ec +79
   - Aksi 6: ph -0.16 | ec +115
   - Aksi 7: ph -0.02 | ec +17 (atau sesuai diskusi)
   - Aksi 8: ph -0.00 | ec +13 (atau sesuai diskusi)

2. **Update Noise & Drift**:
   Menyesuaikan `drift_ph` dan `drift_ec` agar sesuai dengan fluktuasi alami yang terlihat di data manual.

## Verification Plan

### Automated Verification
1. Jalankan `test_env.py` (jika ada) atau skrip pengetesan environment sederhana.
2. Pastikan pemanggilan `env.step(6)` menghasilkan kenaikan EC sekitar 115 unit.
3. Pantau apakah rentang State 0-24 masih relevan dengan perubahan baru ini.
