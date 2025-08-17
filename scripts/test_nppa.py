import csv, json
with open("data/nppa_ceiling_sample.csv") as f:
    rows = list(csv.DictReader(f))
print("rows:", len(rows))
print(json.dumps(rows[:2], indent=2))
