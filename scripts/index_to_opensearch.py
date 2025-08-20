import os
from app.search_service import OpenSearchService


def main():
    os.environ.setdefault("OS_URL", "http://localhost:9200")
    os.environ.setdefault("OS_USER", "admin")
    os.environ.setdefault("OS_PASS", "admin")
    os.environ.setdefault("OS_INDEX_PREFIX", "medbot")
    conn = os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot"
    svc = OpenSearchService(
        os.getenv("OS_URL"),
        os.getenv("OS_USER"),
        os.getenv("OS_PASS"),
        os.getenv("OS_INDEX_PREFIX", "medbot"),
    )
    svc.ensure_index()
    n = svc.bulk_index_from_pg(conn)
    print(f"Indexed {n} docs")


if __name__ == "__main__":
    main()
