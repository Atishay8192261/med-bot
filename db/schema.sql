-- Core brand table (from India catalog)
CREATE TABLE IF NOT EXISTS products_in (
  id SERIAL PRIMARY KEY,
  brand_name TEXT NOT NULL,
  strength TEXT,
  dosage_form TEXT,
  pack TEXT,
  mrp_inr NUMERIC,
  manufacturer TEXT,
  discontinued BOOLEAN DEFAULT FALSE,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- One-to-many salts attached to brand rows
CREATE TABLE IF NOT EXISTS product_salts (
  product_id INTEGER NOT NULL REFERENCES products_in(id) ON DELETE CASCADE,
  salt_name TEXT NOT NULL,
  salt_pos SMALLINT NOT NULL DEFAULT 1,  -- order in combo
  PRIMARY KEY (product_id, salt_pos)
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_products_in_brand ON products_in (brand_name);
CREATE INDEX IF NOT EXISTS idx_products_in_manuf ON products_in (manufacturer);
CREATE INDEX IF NOT EXISTS idx_product_salts_name ON product_salts (salt_name);
