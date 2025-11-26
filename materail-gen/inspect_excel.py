import pandas as pd

try:
    df = pd.read_excel("/Users/danielsamuel/PycharmProjects/RAG/materail-gen/DATABSE.xlsx")
    print("Columns:", df.columns.tolist())
    print("\nFirst 3 rows:")
    print(df.head(3).to_string())
except Exception as e:
    print(f"Error reading excel: {e}")

