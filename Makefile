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
