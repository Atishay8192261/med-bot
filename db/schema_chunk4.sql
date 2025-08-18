-- Jan Aushadhi (PMBJP) generics
CREATE TABLE IF NOT EXISTS janaushadhi_products (
  id SERIAL PRIMARY KEY,
  generic_name TEXT NOT NULL,        -- e.g., "Amoxicillin + Clavulanate"
  strength TEXT,                     -- "625 mg"
  dosage_form TEXT,                  -- "Tablet"
  pack TEXT,                         -- "10"
  mrp_inr NUMERIC,                   -- price
  salt_signature TEXT,               -- computed after mapping
  source_row JSONB,
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_jana_generic ON janaushadhi_products (generic_name);
CREATE INDEX IF NOT EXISTS idx_jana_sig ON janaushadhi_products (salt_signature);

-- NPPA ceiling prices for essential medicines
CREATE TABLE IF NOT EXISTS nppa_ceiling_prices (
  id SERIAL PRIMARY KEY,
  generic_name TEXT NOT NULL,        -- reported name
  strength TEXT,                     -- "500 mg" etc.
  pack TEXT,                         -- pack size if available
  ceiling_price NUMERIC,
  salt_signature TEXT,               -- computed after mapping
  source_row JSONB,
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nppa_generic ON nppa_ceiling_prices (generic_name);
CREATE INDEX IF NOT EXISTS idx_nppa_sig ON nppa_ceiling_prices (salt_signature);

-- Optional helper view to summarize alternatives later
CREATE OR REPLACE VIEW v_products_with_signature AS
SELECT p.id, p.brand_name, p.manufacturer, p.mrp_inr, p.salt_signature
FROM products_in p
WHERE p.salt_signature IS NOT NULL;
