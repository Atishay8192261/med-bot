-- Chunk: External Fallback Caches (DailyMed / openFDA)
-- Idempotent schema additions. Safe to run multiple times.

CREATE TABLE IF NOT EXISTS dailymed_cache_by_ingredient (
  term_norm TEXT PRIMARY KEY,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS openfda_cache_by_ingredient (
  term_norm TEXT PRIMARY KEY,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS dailymed_cache_by_ingredient_fetched_at_idx
  ON dailymed_cache_by_ingredient (fetched_at DESC);
CREATE INDEX IF NOT EXISTS openfda_cache_by_ingredient_fetched_at_idx
  ON openfda_cache_by_ingredient (fetched_at DESC);
