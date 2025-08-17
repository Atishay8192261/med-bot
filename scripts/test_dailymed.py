import requests, json
BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
r = requests.get(BASE, params={"drug_name": "amoxicillin clavulanate"}, timeout=20)
r.raise_for_status()
print(json.dumps(r.json(), indent=2)[:2000])
