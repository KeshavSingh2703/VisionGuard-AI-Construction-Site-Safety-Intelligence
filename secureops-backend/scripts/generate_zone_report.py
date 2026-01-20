import pandas as pd
from pathlib import Path

DATASET_DIR = Path("dataset/restricted_zones")
CSV_FILE = DATASET_DIR / "labels.csv"

def main():
    if not CSV_FILE.exists():
        print("No labels found.")
        return
        
    df = pd.read_csv(CSV_FILE)
    
    print("\n=== Restricted Zone Dataset Report ===")
    print(f"Total Detections: {len(df)}")
    print(f"Unique Images: {df['filename'].nunique()}")
    
    print("\n--- By Class ---")
    print(df['class'].value_counts())
    
    print("\n--- By Zone Status ---")
    print(df['in_zone'].value_counts())
    
    print("\n--- Violation Breakdown ---")
    violations = df[df['in_zone'] == True]
    print(violations.groupby('class').size())
    
    print("\n======================================")

if __name__ == "__main__":
    main()
