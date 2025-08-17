import requests, json
# Get synonyms for acetaminophen (paracetamol)
r = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/acetaminophen/synonyms/JSON", timeout=20)
r.raise_for_status()
print(json.dumps(r.json(), indent=2)[:2000])
