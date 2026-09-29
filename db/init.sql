-- Inventory
CREATE TABLE IF NOT EXISTS products (
    sku          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    price_cents  INTEGER NOT NULL CHECK (price_cents >= 0),
    stock        INTEGER NOT NULL CHECK (stock >= 0)
);

INSERT INTO products (sku, name, price_cents, stock) VALUES
    ('APPLE-001',  'Apple',          120, 100),
    ('BREAD-001',  'Sourdough',      450,  40),
    ('MILK-001',   'Milk 1L',        199,  60),
    ('COFFEE-001', 'Coffee Beans',  1299,  25),
    ('CHOC-001',   'Dark Chocolate', 349,   5)  -- low stock, handy for out-of-stock tests
ON CONFLICT (sku) DO NOTHING;

-- Orders (used by order-service in Phase 3)
CREATE TABLE IF NOT EXISTS orders (
    id           SERIAL PRIMARY KEY,
    sku          TEXT NOT NULL REFERENCES products(sku),
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    total_cents  INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'created',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);