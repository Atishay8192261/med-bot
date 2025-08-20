from __future__ import annotations
import os, re, requests
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

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

def http_get(path: str, params: Dict[str, Any]) -> Any:
    url = f"{API_BASE}{path}"
    r = requests.get(url, params=params, timeout=30)
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


def node_parse(state: AgentState) -> AgentState:
    m = _mem(state.session_id)
    text = state.user_text.strip()
    intent = classify_intent(text)
    brand = state.brand
    if not brand:
        mword = re.search(r"[A-Z][A-Za-z0-9\-]+", text)
        if mword:
            brand = mword.group(0)
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
    sr = http_get("/search", {"query": state.brand, "limit": 3})
    candidates = sr.get("hits", [])
    brand = candidates[0]["brand_name"] if candidates else state.brand
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
    mr = http_get("/monograph", {"signature": state.signature})
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

_graph.set_entry_point("parse")
_graph.add_edge("parse", "resolve_signature")
_graph.add_edge("resolve_signature", "fetch_monograph")
_graph.add_edge("fetch_monograph", "fetch_alternatives")
_graph.add_edge("fetch_alternatives", "compose")
_graph.add_edge("compose", "output")
_graph.add_edge("output", END)

app_graph = _graph.compile()


def run_turn(session_id: str, text: str) -> Dict[str, Any]:
    st = AgentState(session_id=session_id, user_text=text)
    out = app_graph.invoke(st)
    return {
        "brand": out.brand,
        "signature": out.signature,
        "intent": out.intent,
        "answer": out.answer,
        "have_monograph": bool(out.monograph),
        "have_alternatives": bool(out.alternatives),
    }
