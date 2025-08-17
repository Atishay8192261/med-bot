import requests, xmltodict, json
# Example search: "amoxicillin" (broader term)
URL = "https://wsearch.nlm.nih.gov/ws/query"  # MedlinePlus search endpoint
params = {"db":"healthTopics","term":"amoxicillin"}
r = requests.get(URL, params=params, timeout=20)
r.raise_for_status()
data = xmltodict.parse(r.text)
print(json.dumps(data.get("nlmSearchResult", {}) , indent=2)[:2000])
