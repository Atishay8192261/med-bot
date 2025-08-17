import os, requests, json
KEY = os.getenv("OPENFDA_API_KEY", "")
params = {"limit":1}  # Simple search to verify API works
if KEY: params["api_key"] = KEY
r = requests.get("https://api.fda.gov/drug/label.json", params=params, timeout=20)
r.raise_for_status()
print(json.dumps(r.json(), indent=2)[:2000])
