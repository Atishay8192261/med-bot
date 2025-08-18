-- Cache of RxNorm lookups (dedupbed by a normalized key of the term)
CREATE TABLE IF NOT EXISTS rxnorm_cache (
  term_norm TEXT PRIMARY KEY,        -- normalized term key (e.g., "amoxicillin")
  rxcuis TEXT[] NOT NULL,            -- one or more RxCUIs (kept as TEXT for simplicity)
  raw JSONB,                         -- raw response (optional)
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Optional record of per-term errors, to avoid re-querying problematic inputs too often
CREATE TABLE IF NOT EXISTS rxnorm_errors (
  term_norm TEXT PRIMARY KEY,
  reason TEXT,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Product-level mapping/results of RxCUIs and salt_signature
ALTER TABLE products_in
  ADD COLUMN IF NOT EXISTS rxcuis TEXT[];             -- ordered or unique list (we'll store unique sorted)
ALTER TABLE products_in
  ADD COLUMN IF NOT EXISTS salt_signature TEXT;        -- e.g., "197361-310796"
