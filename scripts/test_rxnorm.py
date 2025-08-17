import requests, json, os
BASE = "https://rxnav.nlm.nih.gov/REST"

def approx(term):
    r = requests.get(f"{BASE}/approximateTerm.json", params={"term": term, "maxEntries": 3})
    r.raise_for_status()
    return r.json()

print(json.dumps(approx("amoxicillin clavulanate"), indent=2)[:2000])
