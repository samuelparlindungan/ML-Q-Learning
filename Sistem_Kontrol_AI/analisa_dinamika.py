import pandas as pd
import numpy as np

file_path = r"d:\GitHub\Tes Antigravity+Opencode\dataset_acak_qlearning.csv"
df = pd.read_csv(file_path)

action_names = {
    1: "pH Up Short",
    2: "pH Up Long",
    3: "pH Down Short",
    4: "pH Down Long",
    5: "Nutrisi AB Short",
    6: "Nutrisi AB Long",
    7: "Air Baku Short",
    8: "Air Baku Long",
}

df["Action_Name"] = df["Action"].map(action_names)

summary = (
    df.groupby(["Sesi_Eksperimen", "Action", "Action_Name"])
    .agg({"Delta_pH": ["mean", "std", "count"], "Delta_EC": ["mean", "std"]})
    .reset_index()
)

# Flatten hierarchical columns
summary.columns = [" ".join(col).strip() for col in summary.columns.values]

with open("hasil_dinamika_sesi.md", "w", encoding="utf-8") as f:
    f.write("# Analisis Dinamika Efek Silang (Per Sesi Eksplorasi)\n\n")
    f.write(
        "| Sesi | Aksi | Nama Aksi | Frekuensi | Rata-rata Delta pH (± Std) | Rata-rata Delta EC (± Std) |\n"
    )
    f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
    for index, row in summary.iterrows():
        sesi = str(row["Sesi_Eksperimen"])
        act_id = int(row["Action"])
        act_name = str(row["Action_Name"])
        count = int(row["Delta_pH count"])

        mean_ph = np.round(row["Delta_pH mean"], 3)
        std_ph = np.round(row["Delta_pH std"], 3)
        mean_ec = np.round(row["Delta_EC mean"], 3)
        std_ec = np.round(row["Delta_EC std"], 3)

        if pd.isna(std_ph):
            std_ph = 0.0
        if pd.isna(std_ec):
            std_ec = 0.0

        f.write(
            f"| {sesi} | {act_id} | {act_name} | {count} | {mean_ph:+.3f} ± {std_ph:.3f} | {mean_ec:+.3f} ± {std_ec:.3f} |\n"
        )

print("Selesai.")
