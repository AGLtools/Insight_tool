import pandas as pd
data_dir = r'c:\AGL Analytics\DATA\REPORT\BASE MARS YTD 2026'
files = ['BASE EXPORT 3 MOIS 2026 VS 2025.xlsx', 'BASE IMPORT 3 MOIS 2026 vs 2025.xlsx', 'BASE IMPORT AER 3 MOIS 2026 VS 2025.xlsx']
for fname in files:
    try:
        path = fr'{data_dir}\{fname}'
        df = pd.read_excel(path, nrows=2)
        print(f"\n{fname}:")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Shape: {df.shape}")
    except Exception as e:
        print(f"Error reading {fname}: {e}")
