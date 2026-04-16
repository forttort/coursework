ALTER TABLE products
    ALTER COLUMN parsed_at TYPE TIMESTAMPTZ USING parsed_at AT TIME ZONE 'UTC',
    ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
    ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_seen_in_listing_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS sold_at TIMESTAMPTZ;

UPDATE products
SET first_seen_at = COALESCE(first_seen_at, created_at, CURRENT_TIMESTAMP),
    last_seen_at = COALESCE(last_seen_at, parsed_at, updated_at, created_at, CURRENT_TIMESTAMP),
    last_checked_at = COALESCE(last_checked_at, updated_at, parsed_at, created_at, CURRENT_TIMESTAMP),
    last_seen_in_listing_at = COALESCE(last_seen_in_listing_at, parsed_at, updated_at, created_at, CURRENT_TIMESTAMP),
    status = COALESCE(status, 'active');

ALTER TABLE products
    ALTER COLUMN first_seen_at SET NOT NULL,
    ALTER COLUMN first_seen_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN last_seen_at SET NOT NULL,
    ALTER COLUMN last_seen_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN last_checked_at SET NOT NULL,
    ALTER COLUMN last_checked_at SET DEFAULT CURRENT_TIMESTAMP;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_products_status'
    ) THEN
        ALTER TABLE products
            ADD CONSTRAINT chk_products_status
            CHECK (status IN ('active', 'missing', 'sold', 'unknown'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_last_seen_at ON products(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_products_last_checked_at ON products(last_checked_at);
