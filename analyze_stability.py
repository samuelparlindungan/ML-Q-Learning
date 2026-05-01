import pandas as pd
import numpy as np

# Load dataset
try:
    df = pd.read_csv("d:/GitHub/Tes Antigravity+Opencode/dataset_acak_qlearning.csv")

    # Calculate stats per Action
    stats = df.groupby("Action")[["Delta_pH", "Delta_EC"]].agg(
        ["mean", "std", "min", "max", "count"]
    )

    print("Action Statistics (Detailed) from dataset_acak_qlearning.csv:")
    print("-" * 100)
    print(stats)
    print("-" * 100)

    # Analyze inconsistency (Variance)
    print("\nInconsistency Analysis (Stability):")
    for action in sorted(df["Action"].unique()):
        a_df = df[df["Action"] == action]
        ph_range = a_df["Delta_pH"].max() - a_df["Delta_pH"].min()
        ec_range = a_df["Delta_EC"].max() - a_df["Delta_EC"].min()

        # Check if signs are inconsistent (e.g. some positive, some negative for the same action)
        ph_signs = np.sign(a_df["Delta_pH"][a_df["Delta_pH"] != 0])
        inconsistent_ph = len(set(ph_signs)) > 1 if len(ph_signs) > 0 else False

        print(f"Action {action}:")
        print(
            f"  - pH: Range={ph_range:.2f}, Std={a_df['Delta_pH'].std():.4f}, Mean={a_df['Delta_pH'].mean():.4f}"
        )
        if inconsistent_ph:
            print(f"    [WARNING] pH sign is inconsistent! (Some +, some -)")
        print(
            f"  - EC: Range={ec_range:.2f}, Std={a_df['Delta_EC'].std():.4f}, Mean={a_df['Delta_EC'].mean():.4f}"
        )

except Exception as e:
    print(f"Error: {e}")
