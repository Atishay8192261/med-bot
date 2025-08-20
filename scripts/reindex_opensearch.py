"""Zero-downtime reindex helper (when alias mode enabled).

Steps:
 1. Set OS_USE_ALIAS=1 (so alias indirection is active)
 2. Run this script. It will:
    - Create a new backing index with timestamp
    - Bulk reindex from Postgres
    - Atomically switch alias to new index
    - (Optionally) delete old index if --prune provided
"""
import os, argparse
from app.search_service import OpenSearchService


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prune", action="store_true", help="Delete previous backing index after switch")
    args = ap.parse_args()

    os.environ.setdefault("OS_URL", "http://localhost:9200")
    os.environ.setdefault("OS_USER", "admin")
    os.environ.setdefault("OS_PASS", "admin")
    os.environ.setdefault("OS_USE_ALIAS", "1")
    os.environ.setdefault("OS_INDEX_PREFIX", "medbot")
    alias = os.getenv("OS_INDEX_ALIAS", f"{os.getenv('OS_INDEX_PREFIX','medbot')}-brands")
    conn = os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot"

    svc = OpenSearchService(
        os.getenv("OS_URL"), os.getenv("OS_USER"), os.getenv("OS_PASS"), os.getenv("OS_INDEX_PREFIX", "medbot")
    )
    # Force create new version index (bypassing ensure_index existing alias)
    new_index = svc._resolve_or_create_versioned_index()  # noqa: SLF001
    print(f"Created new backing index: {new_index}")
    n = svc.bulk_index_from_pg(conn)
    print(f"Indexed {n} docs into {new_index}")

    # Switch alias
    client = svc.client
    ali = client.indices.get_alias(name=alias)
    old = list(ali.keys())[0]
    if old == new_index:
        print("Alias already points to new index; nothing to do.")
        return
    actions = [{"remove": {"index": old, "alias": alias}}, {"add": {"index": new_index, "alias": alias}}]
    client.indices.update_aliases({"actions": actions})
    print(f"Alias {alias} switched from {old} -> {new_index}")
    if args.prune:
        client.indices.delete(index=old, ignore=[404])
        print(f"Deleted old index {old}")

if __name__ == "__main__":
    main()
