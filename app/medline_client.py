import os, re, time, json, requests, psycopg
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from lxml import html
from .normalization import norm_term
from .dailymed_client import search_label, get_sections_by_setid
from .openfda_client import fetch_by_ingredient

load_dotenv()

SEARCH_URL = "https://wsearch.nlm.nih.gov/ws/query"
HEADERS = {"User-Agent": "india-med-bot/0.1 (educational only)"}


def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )


def cache_ing_get(term_norm: str) -> Optional[Dict[str, Any]]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT topic_title, topic_url, sections FROM medline_cache_by_ingredient WHERE term_norm=%s",
            (term_norm,),
        )
        row = cur.fetchone()
        if not row:
            return None
        title, url, sections = row
        return {"title": title, "url": url, "sections": sections}


def cache_ing_put(term_norm: str, title: str, url: str, raw: Dict[str, Any], sections: Dict[str, Any]):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          INSERT INTO medline_cache_by_ingredient (term_norm, topic_title, topic_url, raw, sections, updated_at)
          VALUES (%s,%s,%s,%s,%s,NOW())
          ON CONFLICT (term_norm) DO UPDATE SET
            topic_title=excluded.topic_title,
            topic_url=excluded.topic_url,
            raw=excluded.raw,
            sections=excluded.sections,
            updated_at=NOW()
        """,
            (term_norm, title, url, json.dumps(raw), json.dumps(sections)),
        )


def http_get(url: str, params: dict | None = None, tries: int = 3, pause: float = 0.7):
    last = None
    for _ in range(tries):
        try:
            r = requests.get(url, params=params or {}, headers=HEADERS, timeout=25)
            if r.status_code == 200:
                return r
            last = r
        except requests.RequestException as e:
            last = e
        time.sleep(pause)
    if hasattr(last, "raise_for_status"):
        last.raise_for_status()
    raise RuntimeError(f"HTTP failed for {url} params={params} last={last}")


def medline_search(ingredient: str) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """
    Returns (title, url, raw_dict). Strategy:
    1) Search healthTopics for <ingredient>
    2) If no good hit, try "<ingredient> oral", then "<ingredient> tablet", then "<ingredient> medication"
    3) Pick the first document whose title includes the ingredient (case-insensitive); else first doc with a @url.
    """
    import xmltodict, re as _re

    def _try(q: str) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        r = http_get(SEARCH_URL, {"db": "healthTopics", "term": q})
        raw = xmltodict.parse(r.text)
        docs = raw.get("nlmSearchResult", {}).get("list", {}).get("document", []) or []
        if isinstance(docs, dict):
            docs = [docs]

        pat = _re.compile(_re.escape(ingredient), _re.IGNORECASE)
        best_title, best_url = None, None

        for d in docs:
            url = d.get("@url") or None
            title = None
            for c in d.get("content", []) or []:
                if c.get("@name") == "title":
                    title = c.get("#text"); break
            if url and title and pat.search(title or ""):
                return title, url, raw

        for d in docs:
            url = d.get("@url") or None
            if url:
                title = None
                for c in d.get("content", []) or []:
                    if c.get("@name") == "title":
                        title = c.get("#text"); break
                return (title or "MedlinePlus Topic"), url, raw

        return None, None, raw

    queries = [
        ingredient.strip(),
        f"{ingredient} oral",
        f"{ingredient} tablet",
        f"{ingredient} medication",
    ]
    for q in queries:
        t, u, raw = _try(q)
        if u:
            return t, u, raw
    return None, None, raw


SECTION_KEYS = {
    "uses": ["what is", "why is"],
    "how_to_take": ["how should"],
    "precautions": ["precautions", "before taking"],
    "side_effects": ["side effects"],
}


def extract_sections_from_html(html_text: str) -> Dict[str, Any]:
    tree = html.fromstring(html_text)
    sections: Dict[str, str] = {}

    def text_of(node):
        return re.sub(r"\s+", " ", (node.text_content() or "").strip())

    headings = tree.xpath("//h2|//h3")
    for i, h in enumerate(headings):
        title = text_of(h).lower()
        content_nodes = []
        sib = h.getnext()
        while sib is not None and sib.tag not in ("h2", "h3"):
            if sib.tag in ("p", "ul", "ol", "div"):
                content_nodes.append(text_of(sib))
            sib = sib.getnext()
        content = "\n".join([c for c in content_nodes if c])

        bucket = None
        if any(k in title for k in SECTION_KEYS["uses"]):
            bucket = "uses"
        elif any(k in title for k in SECTION_KEYS["how_to_take"]):
            bucket = "how_to_take"
        elif any(k in title for k in SECTION_KEYS["precautions"]):
            bucket = "precautions"
        elif any(k in title for k in SECTION_KEYS["side_effects"]):
            bucket = "side_effects"
        if bucket and content:
            sections[bucket] = content

    return sections


def get_or_fetch_ingredient_topic(ingredient: str) -> Optional[Dict[str, Any]]:
    key = norm_term(ingredient)
    cached = cache_ing_get(key)
    if cached:
        return cached

    title, url, raw = medline_search(ingredient)
    if not url:
        return None
    page = http_get(url, None).text
    sections = extract_sections_from_html(page)
    payload = {"title": title or "MedlinePlus Topic", "url": url, "sections": sections}
    cache_ing_put(key, payload["title"], payload["url"], raw, sections)
    return payload

def get_or_fetch_ingredient_topic_with_fallback(ingredient: str) -> Optional[Dict[str, Any]]:
    primary = get_or_fetch_ingredient_topic(ingredient)
    if primary and primary.get("sections"):
        return primary
    # DailyMed fallback
    hit = search_label(ingredient)
    if hit and (sid := hit.get("setid")):
        sections = get_sections_by_setid(sid)
        if sections:
            return {
                "title": f"{ingredient} (DailyMed)",
                "url": f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={sid}",
                "sections": sections,
            }
    # openFDA fallback
    sec = fetch_by_ingredient(ingredient)
    if sec:
        return {
            "title": f"{ingredient} (openFDA)",
            "url": "https://api.fda.gov/drug/label",
            "sections": sec,
        }
    return primary
