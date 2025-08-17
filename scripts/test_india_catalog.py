import csv, os, json
from pathlib import Path
p = Path("data/india_catalog_sample.csv")
assert p.exists(), "Place a small sample at data/india_catalog_sample.csv"
rows = list(csv.DictReader(p.open()))
print("rows:", len(rows))
print("columns:", list(rows[0].keys()))
print(json.dumps(rows[:2], indent=2))
