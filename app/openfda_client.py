import requests, time
BASE = "https://api.fda.gov/drug/label.json"
UA = {"User-Agent": "india-med-bot/0.1"}

def http_get(url, params=None, tries=3, pause=0.7):
    last = None
    for _ in range(tries):
        try:
            r = requests.get(url, params=params or {}, headers=UA, timeout=25)
            if r.status_code == 200:
                return r
            last = r
        except Exception as e:
            last = e
        time.sleep(pause)
    if hasattr(last, "raise_for_status"):
        last.raise_for_status()
    raise RuntimeError(f"HTTP failed {url} {params} {last}")

def fetch_by_ingredient(ingredient: str):
    q = f'openfda.substance_name:"{ingredient}"'
    r = http_get(BASE, {"search": q, "limit": 1})
    js = r.json()
    results = js.get("results") or []
    if not results:
        return {}
    doc = results[0]
    out = {}
    def first(key):
        v = doc.get(key)
        return v[0] if isinstance(v, list) and v else None
    out["uses"] = first("indications_and_usage")
    out["how_to_take"] = first("dosage_and_administration")
    out["precautions"] = first("warnings") or first("precautions")
    out["side_effects"] = first("adverse_reactions")
    return {k: v for k, v in out.items() if v}
