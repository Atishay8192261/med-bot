import requests, time
BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
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

def search_label(ingredient: str):
    r = http_get(f"{BASE}/spls.json", {"drug_name": ingredient, "pagesize": 1})
    js = r.json()
    data = js.get("data") or []
    return data[0] if data else None

def get_sections_by_setid(setid: str):
    r = http_get(f"{BASE}/spls/{setid}.json")
    js = r.json()
    out = {}
    for sec in js.get("data") or []:
        title = (sec.get("title") or "").lower()
        text = sec.get("text") or ""
        if not text:
            continue
        if "indications" in title or "uses" in title:
            out.setdefault("uses", text)
        if "dosage and administration" in title:
            out.setdefault("how_to_take", text)
        if "warnings" in title or "precautions" in title:
            out.setdefault("precautions", text)
        if "adverse reactions" in title or "side effects" in title:
            out.setdefault("side_effects", text)
    return out
