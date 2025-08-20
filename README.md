# India Medicine Chatbot

Repository skeleton for the India Medicine Chatbot project.

## Structure

- `.venv/` - Python virtual environment
- `.git/` - Git repository
- `.gitignore` - Git ignore patterns
- `requirements.txt` - Python dependencies
- `.env.sample` - Environment variables template
- `notes/` - Build log and decision notes
- `data/` - Raw data files
- `data_cache/` - Cached API responses
- `scripts/` - Test scripts for each data source

## Setup

### Recent Enhancements (Aug 2025)
- Added pagination to `/resolve` (query params: `page`, `limit` up to 100) with a `pagination.more` flag.
- Added parameter validation for `/alternatives` when both `name` and `signature` are supplied; mismatches return 400.
- Added simple in-memory caching for name→signature lookups.
- Expanded drug alias normalization for improved RxNorm mapping.
- Added diagnostic detail to `/health` on DB failure (non-sensitive).
- Introduced jittered backoff & error caching in RxNorm client for resilience.
- Ensure `pdfplumber` is listed in `requirements.txt` for NPPA PDF ingestion.

1. Activate virtual environment: `source .venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.sample` to `.env` and add your API keys

### Chunk 7 (Deterministic Agent + Search)

Run Postgres & (optional) OpenSearch:
```
make db
make os  # optional if using SEARCH_BACKEND=pg
```

Create env file:
```
cp .env.example .env.local
export $(grep -v '^#' .env.local | xargs)
```

Index brands to OpenSearch:
```
make index
```

Start API:
```
make api
```

Quick checks:
```
curl 'http://localhost:8000/search?query=augmentin&limit=3'
curl 'http://localhost:8000/resolve?name=Augmentin'
```

Agent REPL:
```
make repl
# what is augmentin used for?
# any cheaper option?
# side effects?
```

Minimal agent test (server must already be running):
```
make test-agent
```

### Search / Index Ops (Chunk 7+)

Alias mode (optional zero-downtime):
```
export OS_USE_ALIAS=1
export OS_INDEX_ALIAS=medbot-brands
make index  # first time will create versioned backing index + alias
```

Reindex after analyzer change:
```
make reindex           # keeps old index
make reindex prune=1   # (if you modify script to read PRUNE env) or run with --prune via: 
OS_USE_ALIAS=1 python -m scripts.reindex_opensearch --prune
```

Health check includes search backend:
```
curl -s http://localhost:8000/health | jq
```

Fallback: if OpenSearch is unreachable at startup and SEARCH_BACKEND=os, service falls back to PGSearchService automatically.
