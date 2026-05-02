-- Migration: make custom domain names user-scoped
-- Built-in domains (created_by IS NULL) remain globally unique by name.
-- Custom domains are unique per user: UNIQUE(name, created_by).

-- Drop the global unique constraint on name
ALTER TABLE technical_domains DROP CONSTRAINT IF EXISTS technical_domains_name_key;

-- Add user-scoped unique constraint
-- Partial index: only enforce uniqueness among custom domains (created_by IS NOT NULL)
CREATE UNIQUE INDEX IF NOT EXISTS uq_custom_domain_name_per_user
    ON technical_domains (name, created_by)
    WHERE created_by IS NOT NULL;

-- Built-in domains still need global uniqueness (created_by IS NULL)
CREATE UNIQUE INDEX IF NOT EXISTS uq_builtin_domain_name
    ON technical_domains (name)
    WHERE created_by IS NULL;
