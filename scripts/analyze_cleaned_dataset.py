#!/usr/bin/env python3
"""
Dataset Analysis Script
This script analyzes the cleaned_iov.csv dataset to understand its structure,
time range, and proportion of malicious entries.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

def analyze_dataset(csv_path):
    """Analyze the dataset and print useful information"""
    print(f"\n=== ANALYZING DATASET: {csv_path} ===\n")
    
    try:
        # Load the dataset
        df = pd.read_csv(csv_path)
        print(f"Dataset loaded successfully with {len(df)} rows and {len(df.columns)} columns.")
        
        # Check basic information
        print("\n--- BASIC INFORMATION ---")
        print(f"File size: {os.path.getsize(csv_path) / (1024*1024):.2f} MB")
        print(f"Columns: {', '.join(df.columns)}")
        
        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print("\n--- NULL VALUES ---")
            for col, count in null_counts[null_counts > 0].items():
                print(f"Column '{col}' has {count} null values ({count/len(df)*100:.2f}%)")
        else:
            print("\nNo null values found in the dataset.")
        
        # Check timestamp information
        print("\n--- TIMESTAMP ANALYSIS ---")
        if 'timestamp' in df.columns:
            print(f"Timestamp data type: {df['timestamp'].dtype}")
            print(f"Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"Timestamp span: {df['timestamp'].max() - df['timestamp'].min():.2f}")
            
            # Check for uniform distribution
            timestamp_diff = df['timestamp'].diff().dropna()
            print(f"Average time between entries: {timestamp_diff.mean():.4f} seconds")
            print(f"Minimum time between entries: {timestamp_diff.min():.4f} seconds")
            print(f"Maximum time between entries: {timestamp_diff.max():.4f} seconds")
            
            # Check timestamp distribution by hour
            if df['timestamp'].min() >= 0 and df['timestamp'].max() <= 3600:
                print("\nTimestamp distribution by hour segments:")
                hour_segments = pd.cut(df['timestamp'], 
                                      bins=[0, 900, 1800, 2700, 3600], 
                                      labels=['0-15min', '15-30min', '30-45min', '45-60min'])
                segment_counts = hour_segments.value_counts().sort_index()
                for segment, count in segment_counts.items():
                    print(f"  {segment}: {count} entries ({count/len(df)*100:.2f}%)")
        else:
            print("No 'timestamp' column found in dataset.")
        
        # Check malicious information
        print("\n--- MALICIOUS ENTRIES ANALYSIS ---")
        if 'is_malicious' in df.columns:
            malicious_count = df['is_malicious'].sum()
            print(f"Total malicious entries: {malicious_count} ({malicious_count/len(df)*100:.2f}%)")
            print(f"Total normal entries: {len(df) - malicious_count} ({(len(df) - malicious_count)/len(df)*100:.2f}%)")
            
            # Check malicious by time
            if 'timestamp' in df.columns:
                print("\nMalicious distribution by hour segments:")
                malicious_df = df[df['is_malicious'] == 1]
                if not malicious_df.empty and 'timestamp' in malicious_df.columns:
                    m_hour_segments = pd.cut(malicious_df['timestamp'], 
                                           bins=[0, 900, 1800, 2700, 3600], 
                                           labels=['0-15min', '15-30min', '30-45min', '45-60min'])
                    m_segment_counts = m_hour_segments.value_counts().sort_index()
                    for segment, count in m_segment_counts.items():
                        print(f"  {segment}: {count} malicious entries")
        else:
            print("No 'is_malicious' column found in dataset.")
        
        # Data distribution analysis
        print("\n--- DATA SAMPLE ---")
        print("\nFirst 5 rows:")
        print(df.head(5).to_string())
        print("\nLast 5 rows:")
        print(df.tail(5).to_string())
        
        # Generate summary statistics
        print("\n--- NUMERICAL STATISTICS ---")
        print(df.describe().to_string())
        
        print("\n=== ANALYSIS COMPLETE ===\n")
        
        return df
        
    except Exception as e:
        print(f"Error analyzing dataset: {str(e)}")
        return None

if __name__ == "__main__":
    # Use command line argument or default path
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'data/cleaned_iov.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} does not exist.")
        sys.exit(1)
        
    analyze_dataset(csv_path)