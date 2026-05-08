---
inclusion: always
---

# Database Schema Sync Rule

## The Single Source of Truth

`backend/scripts/init_complete.sql` is the **complete, runnable database initialization script**.
It must always reflect the current production schema so a fresh Supabase project can be set up by running this one file.

## Mandatory Rule

**Any change to the database schema MUST also update `init_complete.sql`.**

This includes:
- Adding or dropping a table
- Adding, removing, or renaming a column
- Changing a column type, default, or constraint
- Adding or removing an index
- Adding or removing a trigger or function
- Any `ALTER TABLE` statement

## How to Update

`init_complete.sql` uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` — it is fully idempotent.

When you add a migration, reflect the **final state** in `init_complete.sql`:

| Migration type | What to do in init_complete.sql |
|---|---|
| `ADD COLUMN` | Add the column to the `CREATE TABLE` block |
| `DROP COLUMN` | Remove the column from the `CREATE TABLE` block |
| `ALTER COLUMN` | Update the column definition in place |
| `CREATE TABLE` | Add a new `CREATE TABLE IF NOT EXISTS` block |
| `DROP TABLE` | Remove the entire table block |
| `CREATE INDEX` | Add `CREATE INDEX IF NOT EXISTS` after the table |
| `CREATE FUNCTION` | Update or add the function in the functions section |

Do **not** append `ALTER TABLE` statements to `init_complete.sql` — keep it as a clean schema definition, not a migration log.

## Verification

After updating, mentally verify:
1. A new Supabase project running only `init_complete.sql` would produce the same schema as production.
2. The script has no dependency on execution order issues (tables referenced by FK must be defined before the referencing table).
