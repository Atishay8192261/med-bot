from __future__ import annotations
import os, re, requests
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from app.llm_service import build_llm_service

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
AGENT_LOCAL = os.getenv("AGENT_LOCAL", "1") in ("1","true","yes")

_local_search = None

# --- Simple memory per session_id
_SESSION: Dict[str, Dict[str, Any]] = {}

def _mem(session_id: str) -> Dict[str, Any]:
    return _SESSION.setdefault(session_id, {"last_brand": None, "last_signature": None, "last_intent": None})

# --- very light intent parse (could reuse main intent classifier later)
_INTENT_PATTERNS = {
    "uses": re.compile(r"\b(use|used for|indication|treat)\b", re.I),
    "side_effects": re.compile(r"\b(side ?effects?|adverse)\b", re.I),
    "how_to_take": re.compile(r"\b(how (do i|to) take|dos(?:e|ing)|take it)\b", re.I),
    "precautions": re.compile(r"\b(precaution|warning|avoid)\b", re.I),
    "cheaper": re.compile(r"\b(cheaper|alternative|generic|jan ?aushadhi)\b", re.I),
    "summary": re.compile(r"\b(what is|info|information|about)\b", re.I),
}

def classify_intent(text: str) -> str:
    for k, pat in _INTENT_PATTERNS.items():
        if pat.search(text):
            return k
    return "summary"

# --- HTTP helper

def http_get(path: str, params: Dict[str, Any], allow_404: bool = False) -> Any:
    if AGENT_LOCAL:
        global _local_search
        if _local_search is None:
            from app.search_service import build_search_service
            _local_search = build_search_service()
        from app.main import get_signature_by_name as api_get_signature_by_name  # type: ignore
        from app.main import get_monograph_by_signature as api_get_monograph_by_signature  # type: ignore
        from app.main import salts_by_signature as api_salts_by_signature, brands_by_signature as api_brands_by_signature, jana_by_signature as api_jana_by_signature, nppa_by_signature_or_generic as api_nppa_by_signature_or_generic  # type: ignore
        from app.advise_service import advise_for as api_advise_for  # type: ignore
        # In-process fast path mirrors subset of API endpoints; ignores pagination extras.
        try:
            if path == "/search":
                query = params.get("query")
                limit = int(params.get("limit", 10))
                hits = _local_search.search_brands(query, limit=limit)  # type: ignore
                return {"query": query, "hits": hits}
            if path == "/resolve":
                name = params.get("name")
                sig = api_get_signature_by_name(name)
                if not sig:
                    if allow_404:
                        return None
                    return {"matches": []}
                # Return minimal brand match list using signature lookup brand name if available
                return {"matches": [{"salt_signature": sig, "brand_name": name}]}
            if path == "/monograph":
                sig = params.get("signature")
                doc = api_get_monograph_by_signature(sig)
                if not doc:
                    return None if allow_404 else {}
                return {"title": doc.get("title"), "signature": sig, "sources": doc.get("sources", []), "sections": doc.get("sections", {})}
            if path == "/alternatives":
                sig = params.get("signature")
                salts = api_salts_by_signature(sig)
                brands = api_brands_by_signature(sig)
                jana = api_jana_by_signature(sig)
                ceiling = api_nppa_by_signature_or_generic(sig)
                return {"signature": sig, "salts": salts, "brands": brands, "janaushadhi": jana, "nppa_ceiling_price": ceiling}
            if path == "/advise":
                sig = params.get("signature")
                intent = params.get("intent")
                query = params.get("query")
                ans = api_advise_for(sig, None, intent, False)
                return ans
        except Exception:
            if allow_404:
                return None
            return {}
    url = f"{API_BASE}{path}"
    r = requests.get(url, params=params, timeout=30)
    if allow_404 and r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


class AgentState(BaseModel):
    session_id: str = Field(default="default")
    user_text: str
    brand: Optional[str] = None
    signature: Optional[str] = None
    intent: Optional[str] = None
    monograph: Optional[Dict[str, Any]] = None
    alternatives: Optional[Dict[str, Any]] = None
    answer: Optional[str] = None


_QUESTION_STOPWORDS = {
    "what","any","please","tell","give","show","list","which","how","is","are","do","does","can"
}

def node_parse(state: AgentState) -> AgentState:
    m = _mem(state.session_id)
    text = state.user_text.strip()
    intent = classify_intent(text)
    brand = state.brand
    if not brand:
        # Collect capitalized tokens and choose first non-question stopword
        candidates = re.findall(r"[A-Z][A-Za-z0-9\-]+", text)
        for tok in candidates:
            if tok.lower() not in _QUESTION_STOPWORDS and len(tok) > 2:
                brand = tok
                break
    state.intent = intent
    if not brand:
        brand = m.get("last_brand")
    state.brand = brand
    if state.signature is None:
        state.signature = m.get("last_signature")
    return state


def node_resolve_signature(state: AgentState) -> AgentState:
    if state.signature:
        return state
    if not state.brand:
        state.answer = "Please tell me the medicine brand name."
        return state
    original = state.brand
    sr = http_get("/search", {"query": original, "limit": 5})
    candidates = sr.get("hits", []) if isinstance(sr, dict) else []
    brand = original
    if candidates:
        # Prefer candidate containing the original token
        match = next((c for c in candidates if original.lower() in c.get("brand_name","" ).lower()), None)
        if match:
            brand = match.get("brand_name", original)
        else:
            brand = candidates[0].get("brand_name", original)
    state.brand = brand
    rr = http_get("/resolve", {"name": brand, "limit": 1})
    items = rr.get("matches") if isinstance(rr, dict) else rr
    if not items:
        state.answer = f"I couldn't find {brand} in the catalog."
        return state
    sig = items[0].get("salt_signature")
    state.signature = sig
    m = _mem(state.session_id)
    m["last_brand"] = brand
    m["last_signature"] = sig
    m["last_intent"] = state.intent
    return state


def node_fetch_monograph(state: AgentState) -> AgentState:
    if not state.signature:
        return state
    mr = http_get("/monograph", {"signature": state.signature}, allow_404=True)
    if mr:
        state.monograph = mr
    return state


def node_fetch_alternatives(state: AgentState) -> AgentState:
    if not state.signature:
        return state
    ar = http_get("/alternatives", {"signature": state.signature})
    state.alternatives = ar
    return state


def node_compose(state: AgentState) -> AgentState:
    if not state.signature:
        return state
    adv = http_get(
        "/advise",
        {"signature": state.signature, "query": state.user_text, "intent": state.intent or "summary"},
    )
    state.answer = adv.get("answer") or "Sorry, I don't have enough information."
    if adv.get("alternatives"):
        state.alternatives = adv["alternatives"]
    return state


def node_output(state: AgentState) -> AgentState:  # passthrough
    return state


_graph = StateGraph(AgentState)
_graph.add_node("parse", node_parse)
_graph.add_node("resolve_signature", node_resolve_signature)
_graph.add_node("fetch_monograph", node_fetch_monograph)
_graph.add_node("fetch_alternatives", node_fetch_alternatives)
_graph.add_node("compose", node_compose)
_graph.add_node("output", node_output)
_LLM = build_llm_service()

def node_rewrite_fluency(state: AgentState) -> AgentState:
    if not state.answer or _LLM is None:
        return state
    try:
        state.answer = _LLM.rewrite(state.answer)
    except Exception:
        pass
    return state

_graph.add_node("rewrite_fluency", node_rewrite_fluency)

_graph.set_entry_point("parse")
_graph.add_edge("parse", "resolve_signature")
_graph.add_edge("resolve_signature", "fetch_monograph")
_graph.add_edge("fetch_monograph", "fetch_alternatives")
_graph.add_edge("fetch_alternatives", "compose")
_graph.add_edge("compose", "rewrite_fluency")
_graph.add_edge("rewrite_fluency", "output")
_graph.add_edge("output", END)

app_graph = _graph.compile()


def run_turn(session_id: str, text: str) -> Dict[str, Any]:
    st = AgentState(session_id=session_id, user_text=text)
    out = app_graph.invoke(st)
    # langgraph may return a plain mapping instead of the model instance
    if hasattr(out, "brand"):
        brand = out.brand; signature = out.signature; intent = out.intent; answer = out.answer
        have_m = bool(getattr(out, "monograph", None))
        have_a = bool(getattr(out, "alternatives", None))
    else:  # mapping fallback
        brand = out.get("brand")
        signature = out.get("signature")
        intent = out.get("intent")
        answer = out.get("answer")
        have_m = bool(out.get("monograph"))
        have_a = bool(out.get("alternatives"))
    return {
        "brand": brand,
        "signature": signature,
        "intent": intent,
        "answer": answer,
        "have_monograph": have_m,
        "have_alternatives": have_a,
    }
