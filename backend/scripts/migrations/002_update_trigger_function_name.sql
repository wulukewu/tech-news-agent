-- Migration: Rename trigger function to match design specification
-- Task 1.3: 建立 updated_at 自動更新觸發器
-- This migration renames the generic trigger function to the specific name from design doc

-- Step 1: Drop the existing trigger (we'll recreate it with the new function)
DROP TRIGGER IF EXISTS update_reading_list_updated_at ON reading_list;

-- Step 2: Create the new function with the specific name from design document
CREATE OR REPLACE FUNCTION update_reading_list_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Create the trigger using the new function name
CREATE TRIGGER trigger_update_reading_list_updated_at
    BEFORE UPDATE ON reading_list
    FOR EACH ROW
    EXECUTE FUNCTION update_reading_list_updated_at();

-- Step 4: Drop the old generic function (if it's not used elsewhere)
-- Note: Only drop if no other tables are using it
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Migration complete
-- The trigger now uses the specific function name: update_reading_list_updated_at()
-- Trigger name: trigger_update_reading_list_updated_at
-- This matches the design specification in design.md
