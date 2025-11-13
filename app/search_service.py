from __future__ import annotations
import os
import logging
from typing import List, Dict, Optional, Any
import psycopg
from opensearchpy import OpenSearch, helpers
from datetime import datetime

log = logging.getLogger(__name__)


def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing env: {name}")
    return v


class SearchService:
    def search_brands(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError

    def ensure_index(self) -> None:  # pragma: no cover - optional override
        pass

    def bulk_index_from_pg(self, conn_str: str, batch: int = 5000) -> int:  # pragma: no cover - optional override
        """Optional: index all brands from Postgres (used by OpenSearch backend)."""
        return 0


class PGSearchService(SearchService):
    """Simple fallback using Postgres ILIKE (no pg_trgm needed)."""

    def __init__(self, conn_str: str):
        self.conn_str = conn_str

    def search_brands(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        sql = """
        SELECT p.id, p.brand_name, p.mrp_inr, p.manufacturer, p.salt_signature,
               COALESCE(ARRAY_AGG(ps.salt_name ORDER BY ps.salt_pos)
                        FILTER (WHERE ps.salt_name IS NOT NULL), '{}') AS salts
        FROM products_in p
        LEFT JOIN product_salts ps ON ps.product_id = p.id
        WHERE p.brand_name ILIKE %(q)s
        GROUP BY p.id
        ORDER BY p.brand_name
        LIMIT %(limit)s;
        """
        q = f"%{query}%"
        with psycopg.connect(self.conn_str) as cx:
            rows = cx.execute(sql, {"q": q, "limit": limit}).fetchall()
        return [
            {
                "id": r[0],
                "brand_name": r[1],
                "mrp_inr": r[2],
                "manufacturer": r[3],
                "salt_signature": r[4],
                "salts": r[5] or [],
            }
            for r in rows
        ]


class OpenSearchService(SearchService):
    """OpenSearch implementation with optional alias + versioning.

    Env controls:
      OS_USE_ALIAS=1 to enable alias indirection
      OS_INDEX_ALIAS (alias name; defaults to <prefix>-brands)
      OS_INDEX_PREFIX (base prefix, used when alias disabled)  
    """
    def __init__(self, url: str, user: str, pwd: str, index_prefix: str = "medbot"):
        use_ssl = url.startswith("https://")
        self.client = OpenSearch(
            hosts=[url],
            http_auth=(user, pwd) if user and pwd else None,
            use_ssl=use_ssl,
            verify_certs=False,
        )
        self.prefix = index_prefix
        self.use_alias = os.getenv("OS_USE_ALIAS", "0") in ("1", "true", "yes")
        self.alias = os.getenv("OS_INDEX_ALIAS", f"{index_prefix}-brands")
        # Current target index (resolved in ensure_index)
        self.index = self.alias if not self.use_alias else None  # type: ignore
        self._synonyms = [
            "paracetamol, acetaminophen",
            "amoxycillin, amoxicillin",
            "azithromycine, azithromycin",
            "ranitidine hcl, ranitidine",
            "clavulanic acid, clavulanate, clavulanate potassium",
        ]

    # --- internal helpers ---
    def _index_body(self) -> Dict[str, Any]:
        return {
            "settings": {
                "analysis": {
                    "filter": {
                        "indic_norm": {"type": "indic_normalization"},
                        # Using built-in asciifolding to avoid requiring ICU plugin locally.
                        "my_folding": {"type": "asciifolding", "preserve_original": True},
                        "my_syns": {"type": "synonym_graph", "synonyms": self._synonyms},
                        "edge_2_20": {"type": "edge_ngram", "min_gram": 2, "max_gram": 20},
                    },
                    "analyzer": {
                        "brand_analyzer": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "indic_norm", "my_folding", "my_syns"],
                        },
                        "brand_fuzzy": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "indic_norm", "my_folding"],
                        },
                        "brand_prefix": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "indic_norm", "my_folding", "edge_2_20"],
                        },
                    },
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "brand_name": {
                        "type": "text",
                        "analyzer": "brand_analyzer",
                        "fields": {
                            "kw": {"type": "keyword"},
                            "fuzzy": {"type": "text", "analyzer": "brand_fuzzy"},
                            "prefix": {"type": "text", "analyzer": "brand_prefix"},
                        },
                    },
                    "manufacturer": {"type": "text", "analyzer": "brand_analyzer"},
                    "mrp_inr": {"type": "float"},
                    "salt_signature": {"type": "keyword"},
                    "salts": {"type": "text", "analyzer": "brand_analyzer"},
                }
            },
        }

    def _resolve_or_create_versioned_index(self) -> str:
        # If alias exists, point to it; else create a fresh versioned index and alias it
        if self.client.indices.exists_alias(name=self.alias):  # type: ignore[attr-defined]
            # pick first index behind alias
            ali = self.client.indices.get_alias(name=self.alias)  # type: ignore[attr-defined]
            backing = list(ali.keys())[0]
            return backing
        # create new version index
        version = datetime.utcnow().strftime("v%Y%m%d%H%M%S")
        backing = f"{self.alias}-{version}"
        self.client.indices.create(index=backing, body=self._index_body())  # type: ignore[attr-defined]
        # assign alias
        self.client.indices.put_alias(index=backing, name=self.alias)  # type: ignore[attr-defined]
        return backing

    def ensure_index(self) -> None:
        if self.use_alias:
            if not self.index:
                self.index = self._resolve_or_create_versioned_index()
            return
        # non-alias simple mode
        if not self.client.indices.exists(self.alias):  # type: ignore[attr-defined]
            self.client.indices.create(index=self.alias, body=self._index_body())  # type: ignore[attr-defined]
        self.index = self.alias

    def bulk_index_from_pg(self, conn_str: str, batch: int = 5000) -> int:
        self.ensure_index()
        sql = """
        SELECT p.id, p.brand_name, p.mrp_inr, p.manufacturer, p.salt_signature,
               COALESCE(ARRAY_AGG(ps.salt_name ORDER BY ps.salt_pos)
                        FILTER (WHERE ps.salt_name IS NOT NULL), '{}') AS salts
        FROM products_in p
        LEFT JOIN product_salts ps ON ps.product_id = p.id
        GROUP BY p.id;
        """
        count = 0
        with psycopg.connect(conn_str) as cx:
            cur = cx.execute(sql)
            target_index = self.index or self.alias
            def _docs():
                nonlocal count
                for r in cur:  # type: ignore[assignment]
                    count += 1
                    yield {
                        "_op_type": "index",
                        "_index": target_index,
                        "_id": r[0],
                        "_source": {
                            "id": r[0],
                            "brand_name": r[1],
                            "mrp_inr": float(r[2]) if r[2] is not None else None,
                            "manufacturer": r[3],
                            "salt_signature": r[4],
                            "salts": r[5] or [],
                        },
                    }
            # Larger timeout to avoid ConnectionTimeout on sizable corpora; single final refresh.
            helpers.bulk(
                self.client,
                _docs(),
                chunk_size=batch,
                refresh=False,
                request_timeout=120,
            )
            self.client.indices.refresh(index=target_index)  # type: ignore[attr-defined]
        log.info("Indexed %s documents to %s", count, self.index or self.alias)
        return count

    def search_brands(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        self.ensure_index()
        q = {
            "size": limit,
            "query": {
                "bool": {
                    "should": [
                        {"term": {"brand_name.kw": {"value": query, "boost": 5}}},
                        {"match": {"brand_name": {"query": query, "boost": 3}}},
                        {"match": {"brand_name.fuzzy": {"query": query, "fuzziness": "AUTO"}}},
                        {"match_phrase_prefix": {"brand_name.prefix": {"query": query, "slop": 1}}},
                        {"match": {"salts": {"query": query, "boost": 1}}},
                    ]
                }
            },
        }
        target_index = self.index or self.alias
        res = self.client.search(index=target_index, body=q)  # type: ignore[attr-defined]
        out: List[Dict[str, Any]] = []
        for hit in res.get("hits", {}).get("hits", []):  # type: ignore[assignment]
            src = hit.get("_source", {})
            out.append(
                {
                    "id": src.get("id"),
                    "brand_name": src.get("brand_name"),
                    "mrp_inr": src.get("mrp_inr"),
                    "manufacturer": src.get("manufacturer"),
                    "salt_signature": src.get("salt_signature"),
                    "salts": src.get("salts") or [],
                }
            )
        return out

    def is_alive(self) -> bool:
        try:
            return bool(self.client.ping())  # type: ignore[attr-defined]
        except Exception:
            return False


def build_search_service() -> SearchService:
    backend = os.getenv("SEARCH_BACKEND", "os").lower()
    if backend == "pg":
        conn = os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot"
        return PGSearchService(conn)
    url = os.getenv("OS_URL", "http://localhost:9200")
    user = os.getenv("OS_USER", "admin")
    pwd = os.getenv("OS_PASS", "admin")
    pref = os.getenv("OS_INDEX_PREFIX", "medbot")
    try:
        svc = OpenSearchService(url, user, pwd, pref)
        if hasattr(svc, "client") and svc.client.ping():
            return svc
    except Exception:
        pass
    conn = os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot"
    log.warning("OpenSearch unavailable, falling back to PGSearchService")
    return PGSearchService(conn)
