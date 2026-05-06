# Discord ID Validation Fix

## Problem

The application was experiencing errors when sending DM notifications to users:

```
Invalid discord_id format: test_user_a49fe291, skipping
Failed to send personalized digest to user 17008854713740992329: 400 Bad Request
In user_id: snowflake value should be less than or equal to 9223372036854775807
```

### Root Causes

1. **Invalid Test Data**: Tests were creating users with non-numeric `discord_id` values like `test_user_{uuid.hex}`, which contains letters
2. **Insufficient Validation**: The user repository only validated that `discord_id` was a non-empty string, not that it was numeric
3. **No Range Validation**: Discord IDs are 64-bit signed integers (snowflakes) with a maximum value of `9223372036854775807`

## Solution

### 1. Enhanced Validation in User Repository

Updated `backend/app/repositories/user.py` to validate:

- ✅ Discord ID must be numeric (only digits)
- ✅ Discord ID must be within valid snowflake range (≤ 9223372036854775807)
- ✅ Applied to both user creation and updates

```python
# Discord IDs must be numeric (snowflake IDs are 64-bit integers)
if not discord_id.strip().isdigit():
    raise ValidationError(
        "Invalid discord_id: must be a numeric string (Discord snowflake ID)",
        error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
        details={"field": "discord_id", "value": discord_id},
    )

# Validate Discord snowflake range (must fit in 64-bit signed integer)
try:
    discord_id_int = int(discord_id.strip())
    if discord_id_int > 9223372036854775807:  # Max 64-bit signed int
        raise ValidationError(
            "Invalid discord_id: value exceeds maximum Discord snowflake ID",
            error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
            details={"field": "discord_id", "value": discord_id, "max": 9223372036854775807},
        )
except ValueError:
    raise ValidationError(
        "Invalid discord_id: must be a valid integer",
        error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
        details={"field": "discord_id", "value": discord_id},
    )
```

### 2. Test Helper for Valid Discord IDs

Created `backend/tests/helpers/discord_id_generator.py` with utilities to generate valid test Discord IDs:

```python
from tests.helpers.discord_id_generator import generate_test_discord_id

# Generate a valid Discord ID for testing
discord_id = generate_test_discord_id()
```

### 3. Database Cleanup Script

Created `backend/scripts/cleanup_invalid_users.py` to remove existing invalid users:

```bash
# Load environment variables
source .env

# Run cleanup script
python3 backend/scripts/cleanup_invalid_users.py
```

## Discord Snowflake Format

Discord IDs use Twitter's snowflake format - a 64-bit integer with embedded metadata:

```
 64                                          22     17     12          0
  ┌─────────────────────────────────────────┬──────┬──────┬───────────┐
  │          Timestamp (42 bits)            │Worker│Process│ Increment │
  │    (milliseconds since Discord epoch)   │(5bit)│(5bit) │  (12 bit) │
  └─────────────────────────────────────────┴──────┴──────┴───────────┘
```

- **Timestamp**: Milliseconds since Discord epoch (2015-01-01 00:00:00 UTC)
- **Worker ID**: Internal worker ID (0-31)
- **Process ID**: Internal process ID (0-31)
- **Increment**: Sequence number (0-4095)

**Valid Range**: `0` to `9223372036854775807` (max 64-bit signed integer)

## Migration Guide for Tests

### Before (Invalid)

```python
# ❌ This creates invalid Discord IDs
discord_id = f"test_user_{uuid4().hex}"  # Contains letters!
discord_id = f"test_user_{os.urandom(4).hex()}"  # Contains letters!
```

### After (Valid)

```python
# ✅ Use the helper function
from tests.helpers.discord_id_generator import generate_test_discord_id

discord_id = generate_test_discord_id()  # Returns valid numeric string
```

### Alternative (Simple)

```python
# ✅ Simple numeric ID
import random
discord_id = str(random.randint(100000000000000000, 999999999999999999))
```

## Testing the Fix

1. **Run validation tests**:

   ```bash
   pytest backend/tests/test_repositories.py -k discord_id
   ```

2. **Clean up invalid data**:

   ```bash
   python3 backend/scripts/cleanup_invalid_users.py
   ```

3. **Verify DM notifications work**:
   ```bash
   # Check logs for "Invalid discord_id format" messages
   docker-compose logs backend | grep "Invalid discord_id"
   ```

## Prevention

- All new tests must use `generate_test_discord_id()` helper
- Repository validation will reject invalid Discord IDs at creation time
- CI/CD should run cleanup script before deployment to catch any test pollution

## References

- [Discord Snowflake Documentation](https://discord.com/developers/docs/reference#snowflakes)
- [Twitter Snowflake](https://github.com/twitter-archive/snowflake/tree/snowflake-2010)
