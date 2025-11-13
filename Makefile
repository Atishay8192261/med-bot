.PHONY: db os api index repl test-agent

db:
	docker compose up -d

os:
	docker compose -f docker-compose.opensearch.yml up -d

api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

index:
	SEARCH_BACKEND=os python -m scripts.index_to_opensearch

repl:
	python -m scripts.run_agent_repl

test-agent:
	pytest -q tests/test_agent_basic.py -k simple_flow

reindex:
	OS_USE_ALIAS=1 python -m scripts.reindex_opensearch


smoke-search:
	curl -s 'http://localhost:8000/health' | jq '.search_backend,.search_ok'
	curl -s 'http://localhost:8000/search?query=para&limit=3' | jq '.'

# Fast deterministic unit-ish tests (no network / no OpenAI required)
test-fast:
	pytest -q tests/test_intent_and_safety.py tests/test_price_summary.py

# Run LLM rewrite test (requires OPENAI_API_KEY + LLM_ENABLED=1)
test-llm:
	LLM_ENABLED=1 pytest -q tests/test_llm_rewrite.py

# ---------------- Ingestion / Data Ops ----------------

# Ingest sample (small) datasets only (fast smoke)
ingest-sample: ## Sample India catalog only
	DB_HOST=localhost DB_PORT=5432 DB_NAME=medbot DB_USER=appuser DB_PASS=apppass \
		python scripts/ingest_india_catalog.py

# Ingest full India catalog (expects raw file present)
ingest-india-full:
	DB_HOST=localhost DB_PORT=5432 DB_NAME=medbot DB_USER=appuser DB_PASS=apppass \
		python scripts/ingest_india_catalog_full.py

# Ingest Janaushadhi (generic govt price list)
ingest-jana:
	DB_HOST=localhost DB_PORT=5432 DB_NAME=medbot DB_USER=appuser DB_PASS=apppass \
		python scripts/ingest_janaushadhi.py || python scripts/ingest_janaushadhi_csv.py

# Ingest NPPA ceiling prices (CSV or PDF parser depending on script available)
ingest-nppa:
	DB_HOST=localhost DB_PORT=5432 DB_NAME=medbot DB_USER=appuser DB_PASS=apppass \
		python scripts/ingest_nppa.py || python scripts/ingest_nppa_pdf.py

# Compute RxNorm-based salt signatures (network calls to RxNav)
compute-signatures:
	DB_HOST=localhost DB_PORT=5432 DB_NAME=medbot DB_USER=appuser DB_PASS=apppass \
		PYTHONPATH=. python scripts/compute_signatures.py

# Map signatures to reference datasets (if script exists)
map-refs:
	DB_HOST=localhost DB_PORT=5432 DB_NAME=medbot DB_USER=appuser DB_PASS=apppass \
		PYTHONPATH=. python scripts/map_signatures_for_refs.py --targets nppa jana || true

# Full seed pipeline (idempotent-ish; uses ON CONFLICT DO NOTHING in scripts)
seed-full: ingest-india-full ingest-jana ingest-nppa compute-signatures map-refs
	@echo 'Seed pipeline complete.'

# Quick seed (sample only + signatures)
seed-sample: ingest-sample compute-signatures
	@echo 'Sample seed complete.'

# Basic counts to verify ingestion
verify-counts:
	docker exec -it medbot_db psql -U appuser -d medbot -c "SELECT 'products_in', count(*) FROM products_in;" || true
	docker exec -it medbot_db psql -U appuser -d medbot -c "SELECT 'product_salts', count(*) FROM product_salts;" || true
	docker exec -it medbot_db psql -U appuser -d medbot -c "SELECT 'janaushadhi_products', count(*) FROM janaushadhi_products;" || true
	docker exec -it medbot_db psql -U appuser -d medbot -c "SELECT 'nppa_ceiling_prices', count(*) FROM nppa_ceiling_prices;" || true

# Create a compressed custom-format backup (requires pg_dump in container image)
backup:
	docker exec medbot_db pg_dump -U appuser -d medbot -Fc > backup_medbot_`date +%Y%m%d_%H%M%S`.dump

# Restore from a custom-format dump (usage: make restore DUMP=backup_medbot_xxx.dump)
restore:
	@if [ -z "$(DUMP)" ]; then echo 'Specify DUMP=filename.dump'; exit 1; fi
	cat $(DUMP) | docker exec -i medbot_db pg_restore -U appuser -d medbot --clean --if-exists

# --- External fallback chunk helpers ---
.PHONY: migrate-ext test-ext

migrate-ext:
	psql "$$DATABASE_URL" -f db/schema_chunk_ext_fallbacks.sql

test-ext:
	pytest -q tests/test_monograph_fallback_merge.py tests/test_external_gating.py
