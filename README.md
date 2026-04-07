# Q-Learning untuk Kontrol pH dan EC Hidroponik

Implementasi Q-Learning sesuai spesifikasi dokumen B600 dengan **Adaptive Learning Rate** untuk stabilitas optimal.

## 📁 Struktur File

```
tes training/
├── env_ph_ec.py              # Environment (25 states, 9 actions)
├── qlearning_agent.py        # Q-Learning Agent (Adaptive Learning)
├── train.py                  # Training script (1500 episodes)
├── visualize.py              # Visualisasi hasil (6 grafik)
├── README.md                 # Dokumentasi
├── STABILITAS_Q_VALUE.md     # Penjelasan stabilitas Q-value
└── output/                   # Hasil training
    ├── Q_table.npy           # Q-table terlatih (25×9)
    ├── policy.json           # Policy dalam format JSON
    ├── reward_log.npy        # Log reward per episode
    ├── step_log.npy          # Log steps per episode
    ├── qmax_log.npy          # Log Q-max per episode
    ├── alpha_log.npy         # Log learning rate per episode
    ├── state_visit.npy       # Frekuensi kunjungan state
    ├── action_count.npy      # Frekuensi penggunaan action
    └── trajectory.npy        # Trajectory lengkap
```

## 🎯 Spesifikasi (Sesuai B600)

### State Space (Tabel 3.3)

- **25 states**: 5 pH levels × 5 EC levels
- **Target**: State 13 (pH=2, EC=2)
- **Critical States**: [0,1,2,3,4,5,9,10,14,15,19,20,21,22,23,24]

### Action Space (Tabel 3.4)

| ID  | Aksi           | Efek      |
| --- | -------------- | --------- |
| 0   | IDLE           | Tidak ada |
| 1   | pH Up Short    | +0.5      |
| 2   | pH Up Long     | +1.0      |
| 3   | pH Down Short  | -0.5      |
| 4   | pH Down Long   | -1.0      |
| 5   | Nutrisi Short  | +0.5      |
| 6   | Nutrisi Long   | +1.0      |
| 7   | Air Baku Short | -0.5      |
| 8   | Air Baku Long  | -1.0      |

### Reward Function (Tabel 3.6)

| Zona           | Reward | States                          |
| -------------- | ------ | ------------------------------- |
| Kritis Ekstrem | -120   | 1,5,21,25                       |
| Kritis         | -80    | 2,3,4,6,10,11,15,16,20,22,23,24 |
| Transisi       | -5     | 7,9,17,19                       |
| Sub-Optimal    | +10    | 8,12,14,18                      |
| Target         | +50    | 13                              |

### Hyperparameters (Optimized)

```python
# Learning Rate (Adaptive)
alpha = 0.1              # Initial learning rate
alpha_decay = 0.9995     # Decay rate
alpha_min = 0.01         # Minimum learning rate

# Exploration (Epsilon-Greedy)
epsilon = 1.0            # Initial exploration (100%)
epsilon_decay = 0.995    # Decay rate
epsilon_min = 0.01       # Minimum exploration (1%)

# Q-Learning
gamma = 0.95             # Discount factor
episodes = 1500          # Training episodes
max_steps = 40           # Max steps per episode
```

## 🚀 Cara Menggunakan

### Training

```bash
cd "tes training"
python train.py
```

**Output Console**:

```
Critical states: [0, 1, 2, 3, 4, 5, 9, 10, 14, 15, 19, 20, 21, 22, 23, 24]
Reward grid:
 [[-120  -80  -80  -80 -120]
  [ -80   -5   10   -5  -80]
  [ -80   10   50   10  -80]
  [ -80   -5   10   -5  -80]
  [-120  -80  -80  -80 -120]]
Initial: Alpha=0.100, Epsilon=1.000

Ep 150  | AvgR:-1307.4 | Eps:0.471 | Alpha:0.0928
Ep 300  | AvgR:-42.3   | Eps:0.222 | Alpha:0.0861
Ep 450  | AvgR:11.2    | Eps:0.105 | Alpha:0.0798
Ep 600  | AvgR:28.7    | Eps:0.049 | Alpha:0.0741
Ep 750  | AvgR:36.4    | Eps:0.023 | Alpha:0.0687
Ep 900  | AvgR:34.3    | Eps:0.011 | Alpha:0.0638
Ep 1050 | AvgR:35.0    | Eps:0.010 | Alpha:0.0591
Ep 1200 | AvgR:32.1    | Eps:0.010 | Alpha:0.0549
Ep 1350 | AvgR:29.8    | Eps:0.010 | Alpha:0.0509
Ep 1500 | AvgR:33.9    | Eps:0.010 | Alpha:0.0472

✅ TRAINING SELESAI!
Final: Alpha=0.0472, Epsilon=0.010
```

### Visualisasi

```bash
python visualize.py
```

**6 Grafik yang Ditampilkan**:

1. **Reward Convergence** - Konvergensi reward dengan moving average
2. **Q-max Convergence** - Stabilitas Q-value dengan moving average
3. **Alpha Decay** - Penurunan learning rate
4. **Step Efficiency** - Efisiensi mencapai target
5. **State Visitation Heatmap** - Distribusi kunjungan state
6. **Action Distribution** - Frekuensi penggunaan action

## 🔬 Fitur Utama

### ✅ **Adaptive Learning Rate**

```python
# Learning rate menurun berdasarkan:
# 1. Global decay (alpha_decay)
# 2. Visit count per state-action pair

adaptive_alpha = alpha / (1 + 0.001 * visit_count[state, action])
```

**Keuntungan**:

- Q-values lebih stabil di akhir training
- State yang sering dikunjungi → learning lebih lambat
- Mencegah oscillation

### ✅ **Dual Decay Strategy**

```python
agent.decay_epsilon()  # Kurangi exploration
agent.decay_alpha()    # Kurangi learning rate
```

**Hasil**:

- Epsilon: 1.0 → 0.01 (exploration berkurang)
- Alpha: 0.1 → 0.047 (learning lebih stabil)

### ✅ **Moving Average Visualization**

```python
window = 50
moving_avg = np.convolve(data, np.ones(window)/window, mode="valid")
```

**Manfaat**:

- Melihat trend konvergensi lebih jelas
- Mengurangi noise dari fluktuasi
- Validasi stabilitas training

## 📊 Hasil Training

### **Konvergensi Reward**

```
Episode    | Avg Reward | Status
-----------|------------|------------------
0-150      | -1307.4    | Exploration tinggi
150-300    | -42.3      | Mulai belajar
300-600    | 11.2-28.7  | Konvergen positif
600-1500   | 29.8-36.4  | Stabil optimal
```

### **Stabilitas Q-Value**

- ✅ Q-max dengan moving average menunjukkan konvergensi
- ✅ Fluktuasi berkurang signifikan setelah episode 900
- ✅ Learning rate menurun → perubahan lebih kecil

### **Efisiensi**

- ✅ Steps menurun seiring training (lebih efisien)
- ✅ Agent menemukan path optimal ke target
- ✅ Exploration-exploitation balance optimal

## 📝 Output Files

### policy.json

```json
"state_13": {
  "pH_index": 2,
  "EC_index": 2,
  "best_action": 0,
  "q_values": [0.0, 0.0, ...],
  "max_q": 0.0
}
```

### Reward Grid (5×5)

```
[[-120  -80  -80  -80 -120]
 [ -80   -5   10   -5  -80]
 [ -80   10   50   10  -80]
 [ -80   -5   10   -5  -80]
 [-120  -80  -80  -80 -120]]
```

## ❓ FAQ: Stabilitas Q-Value

**Q: Mengapa Q-value masih berfluktuasi?**

A: Fluktuasi kecil adalah **NORMAL** karena:

1. Environment stochastic (drift + noise)
2. Exploration minimum (1%) masih aktif
3. Adaptive learning tetap responsif

**Lihat**: `STABILITAS_Q_VALUE.md` untuk penjelasan lengkap

**Q: Bagaimana tahu training sudah konvergen?**

A: Indikator konvergensi:

- ✅ Reward stabil (tidak naik/turun drastis)
- ✅ Q-max moving average flat
- ✅ Alpha sudah kecil (<0.05)
- ✅ Epsilon minimum tercapai

## ✅ Kesesuaian dengan B600

- ✅ State Space (Tabel 3.3): 25 states
- ✅ Action Space (Tabel 3.4): 9 actions
- ✅ Q-Table (Tabel 3.5): 25×9 matrix
- ✅ Reward Function (Tabel 3.6): Zone-based
- ✅ Training (3.5.1): 1500 episodes
- ✅ Critical States Initialization
- ✅ Hyperparameters optimized
- ✅ **BONUS**: Adaptive learning rate untuk stabilitas

## 📦 Dependencies

```bash
pip install numpy matplotlib gymnasium
```

## 📚 Referensi

- **Dokumen B600**: Spesifikasi state, action, reward
- **Sutton & Barto (2018)**: Q-Learning theory
- **STABILITAS_Q_VALUE.md**: Analisis stabilitas lengkap
