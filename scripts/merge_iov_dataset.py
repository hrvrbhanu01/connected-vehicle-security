import pandas as pd
import os
from tqdm import tqdm  # For progress bars

# Configuration (UPDATE THESE PATHS!)
DATASET_DIR = "data/CICIoV2024"  # Path to unzipped dataset folder
OUTPUT_FILE = "data/raw_iov.csv"
FORMAT = "decimal"  # "binary", "decimal", or "hexadecimal"

def merge_dataset():
    dfs = []
    print(f"⏳ Merging {FORMAT} format files...")
    
    for filename in tqdm(os.listdir(f"{DATASET_DIR}/{FORMAT}")):
        if filename.endswith(".csv"):
            # Extract attack type from filename (e.g., "decimal_DoS.csv" -> "DoS")
            attack_type = filename.split('_')[1].split('.')[0]
            
            # Read file
            filepath = os.path.join(DATASET_DIR, FORMAT, filename)
            df = pd.read_csv(filepath)
            
            # Add attack labels
            df['attack_type'] = attack_type
            df['is_malicious'] = 0 if attack_type == "benign" else 1
            
            dfs.append(df)
    
    # Combine all DataFrames
    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved merged data to {OUTPUT_FILE}")
    print(f"Total records: {len(merged_df):,}")
    print("Sample data:\n", merged_df.head())

if __name__ == "__main__":
    merge_dataset()