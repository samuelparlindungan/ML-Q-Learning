"""
build_project_md.py
===================
Script untuk membuat 1 file .md yang isinya adalah
copy-paste langsung dari semua file proyek.
"""

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
V6_DIR     = os.path.join(BASE_DIR, "output", "v6_final")
TXT_DIR    = os.path.join(V6_DIR, "text_version")
OUT_FILE   = os.path.join(BASE_DIR, "output", "PROJECT_ALL_FILES.md")

def read_file(path, max_lines=None):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"\n... (dipotong, total lebih dari {max_lines} baris) ...\n")
                        break
                    lines.append(line)
                return "".join(lines)
            return f.read()
    except Exception as e:
        return f"[ERROR membaca file: {e}]"

sections = []

# ==============================
# KODE SUMBER .py
# ==============================
py_files = {
    "env_ph_ec.py":          os.path.join(SCRIPT_DIR, "env_ph_ec.py"),
    "qlearning_agent.py":    os.path.join(SCRIPT_DIR, "qlearning_agent.py"),
    "main_training.py":      os.path.join(SCRIPT_DIR, "main_training.py"),
    "random_explorer_v1.py": os.path.join(SCRIPT_DIR, "random_explorer_v1.py"),
    "main_auto_control.py":  os.path.join(SCRIPT_DIR, "main_auto_control.py"),
}

sections.append("# KUMPULAN ISI FILE — PROYEK HIDROPONIK RL Q-LEARNING\n\n---\n\n")
sections.append("## BAGIAN 1: KODE SUMBER PYTHON (.py)\n\n")

for name, path in py_files.items():
    sections.append(f"### `{name}`\n\n")
    sections.append(f"```python\n{read_file(path)}\n```\n\n---\n\n")

# ==============================
# FILE DATA .csv
# ==============================
csv_files = {
    "dataset_acak_qlearning.csv":  os.path.join(BASE_DIR, "dataset_acak_qlearning.csv"),
    "data_transisi_otomatis.csv":  os.path.join(BASE_DIR, "output", "data_transisi_otomatis.csv"),
}

sections.append("## BAGIAN 2: DATA EKSPERIMEN (.csv)\n\n")
for name, path in csv_files.items():
    sections.append(f"### `{name}`\n\n")
    sections.append(f"```\n{read_file(path)}\n```\n\n---\n\n")

# ==============================
# FILE TRAINING .npy (versi .txt)
# ==============================
npy_txt_files = {
    "Q_table.txt":        os.path.join(TXT_DIR, "Q_table.txt"),
    "state_visit.txt":    os.path.join(TXT_DIR, "state_visit.txt"),
    "action_count.txt":   os.path.join(TXT_DIR, "action_count.txt"),
    "reward_log.txt":     os.path.join(TXT_DIR, "reward_log.txt"),
    "step_log.txt":       os.path.join(TXT_DIR, "step_log.txt"),
    "qmax_log.txt":       os.path.join(TXT_DIR, "qmax_log.txt"),
    "alpha_log.txt":      os.path.join(TXT_DIR, "alpha_log.txt"),
}

# Batas baris untuk log besar (10.000 baris):
# Q_table dan kecil-kecil tampilkan semua, log besar tampilkan semua juga.
sections.append("## BAGIAN 3: DATA TRAINING MODEL v6_final (.npy → .txt)\n\n")
sections.append("> File `.npy` adalah format biner. Isi di bawah ini adalah konversi teks.\n\n")

for name, path in npy_txt_files.items():
    sections.append(f"### `{name}` (dari `{name.replace('.txt', '.npy')}`)\n\n")
    sections.append(f"```\n{read_file(path)}\n```\n\n---\n\n")

# Tulis semua ke file .md
with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.writelines(sections)

print(f"\n[SELESAI] File MD berhasil dibuat:")
print(f"  {OUT_FILE}")
print(f"  Ukuran: {os.path.getsize(OUT_FILE) / 1024:.1f} KB")
