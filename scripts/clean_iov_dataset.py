import pandas as pd
from datetime import datetime

def preprocess_iov(input_path, output_path):
    # Load the raw data
    df = pd.read_csv(input_path)
    
    print("Original columns:", df.columns.tolist())  # Debug
    
    # 1. Standardize column names
    df = df.rename(columns={
        "ID": "can_id",
        "category": "attack_category",
        "specific_class": "attack_type"
    })
    
    # 2. Combine DATA columns into single CAN payload
    data_cols = [col for col in df.columns if col.startswith('DATA_')]
    df['payload'] = df[data_cols].apply(
        lambda x: ''.join(f"{int(val):02X}" for val in x), 
        axis=1
    )
    
    # 3. Add timestamp (since original doesn't have one)
    df['timestamp'] = [int(datetime.now().timestamp()) - len(df) + i for i in range(len(df))]
    
    # 4. Convert label to binary (0=benign, 1=attack)
    df['is_malicious'] = df['label'].apply(lambda x: 0 if x == "BENIGN" else 1)
    
    # 5. Select final columns
    clean_df = df[[
        'timestamp',
        'can_id',
        'payload',
        'attack_category',
        'attack_type',
        'is_malicious'
    ]]
    
    clean_df.to_csv(output_path, index=False)
    print(f"Cleaned data saved to {output_path}")
    print("Sample output:", clean_df.head())

if __name__ == "__main__":
    preprocess_iov(
        input_path="data/raw_iov.csv", 
        output_path="data/cleaned_iov.csv"
    )