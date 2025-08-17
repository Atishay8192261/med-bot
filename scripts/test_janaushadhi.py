import pandas as pd, json, pathlib
p = pathlib.Path("data/jan_aushadhi_sample.xlsx")
assert p.exists(), "Create data/jan_aushadhi_sample.xlsx with 2-3 rows."
df = pd.read_excel(p)
print("rows:", len(df))
print(json.dumps(df.head(2).to_dict(orient="records"), indent=2))
