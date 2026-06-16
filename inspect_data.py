import pandas as pd
import os

path = r'c:\Users\BenjJavier\OneDrive - bolttech\Documents\Copilot\Created\training_dashboard\dashboard_copy.xlsx'

print(f"File exists: {os.path.exists(path)}")
print(f"File size: {os.path.getsize(path):,} bytes")
print("=" * 80)

xls = pd.ExcelFile(path)
print(f"\nSheets found: {xls.sheet_names}")
print("=" * 80)

for sheet in xls.sheet_names:
    df = pd.read_excel(path, sheet_name=sheet)
    print(f"\n--- Sheet: '{sheet}' ---")
    print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"\n  Columns:")
    for i, col in enumerate(df.columns):
        dtype = df[col].dtype
        non_null = df[col].notna().sum()
        sample = df[col].dropna().iloc[0] if non_null > 0 else "N/A"
        sample_str = str(sample)[:50]
        print(f"    {i+1:2d}. {col:<40} | {str(dtype):<15} | Non-null: {non_null:>4} | Sample: {sample_str}")
    print()
