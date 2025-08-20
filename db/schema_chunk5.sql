CREATE TABLE IF NOT EXISTS advise_logs (
  id BIGSERIAL PRIMARY KEY,
  asked_at TIMESTAMP DEFAULT NOW(),
  user_query TEXT,
  name TEXT,
  signature TEXT,
  intent TEXT,
  success BOOLEAN,
  notes TEXT
);
