-- Cache by normalized ingredient term (so a single fetch can serve many brands)
CREATE TABLE IF NOT EXISTS medline_cache_by_ingredient (
  term_norm TEXT PRIMARY KEY,      -- e.g., "amoxicillin", "clavulanate potassium"
  topic_title TEXT,
  topic_url TEXT,
  raw JSONB,
  sections JSONB,                  -- parsed: uses, how_to_take, precautions, side_effects
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Cache by salt_signature (e.g., "21216-723" for combos)
CREATE TABLE IF NOT EXISTS medline_monograph_by_signature (
  salt_signature TEXT PRIMARY KEY,
  title TEXT,
  sources JSONB,                   -- list of topic URLs used to compose
  sections JSONB,                  -- combined/stitched sections for the combo
  updated_at TIMESTAMP DEFAULT NOW()
);
