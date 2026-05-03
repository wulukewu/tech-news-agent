# Scheduler Initialization Fix

## Problem

The backend was crashing on startup with:

```
AttributeError: 'NoneType' object has no attribute 'timezone'
```

And later:

```
AttributeError: 'NoneType' object has no attribute 'start'
```

## Root Cause

The scheduler was being initialized at module import time:

```python
scheduler = AsyncIOScheduler(timezone=settings.timezone)
```

This caused two issues:

1. **Settings not loaded**: When `settings` was `None` (due to missing environment variables), accessing `settings.timezone` caused an immediate crash
2. **Python scoping issue**: Even after fixing the initialization timing, `from app.tasks.scheduler import scheduler` created a static binding to the `None` value that didn't update when the global variable changed

## Solution

### 1. Lazy Initialization

Changed the scheduler to be initialized lazily in `setup_scheduler()`:

```python
# Global scheduler instance (initialized lazily)
_scheduler: Optional[AsyncIOScheduler] = None

def setup_scheduler():
    global _scheduler

    if settings is None:
        raise RuntimeError("Settings not loaded...")

    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=settings.timezone)

    # ... register jobs ...
    return _scheduler
```

### 2. Dynamic Attribute Access

Implemented `__getattr__` for backward compatibility with existing imports:

```python
def __getattr__(name: str):
    """
    Dynamic attribute access for backward compatibility.
    Allows 'from app.tasks.scheduler import scheduler' to work correctly.
    """
    if name == "scheduler":
        return _scheduler
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
```

This ensures that `from app.tasks.scheduler import scheduler` always returns the current value of `_scheduler`, even after it's been initialized.

### 3. Getter Function

Added a getter function for explicit access:

```python
def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the global scheduler instance."""
    return _scheduler
```

### 4. Improved Error Handling

Enhanced configuration loading to fail fast in production with clear error messages:

```python
# In config.py
try:
    if os.getenv("SKIP_CONFIG_LOAD") != "1":
        settings = load_settings()
        if settings is None:
            raise ConfigurationError("Settings loaded but returned None")
except ConfigurationError as e:
    print(f"Configuration Error: {e}", file=sys.stderr)
    if os.getenv("APP_ENV") == "prod":
        raise  # Fail fast in production
    settings = None
```

## Files Modified

1. **backend/app/tasks/scheduler.py**
   - Changed `scheduler` to `_scheduler` (private)
   - Added `get_scheduler()` function
   - Added `__getattr__` for dynamic access
   - Added comprehensive logging in `setup_scheduler()`
   - Updated all internal references to use `_scheduler`

2. **backend/app/core/config.py**
   - Improved error handling for configuration loading
   - Added fail-fast behavior in production
   - Better error messages for missing environment variables

3. **backend/app/main.py**
   - Updated imports to use `get_scheduler`
   - Added error handling around scheduler startup
   - Safe scheduler shutdown check

## Testing

The fix was verified with:

1. **Import test**: Module can be imported without crash when settings is None
2. **Initialization test**: Scheduler is properly initialized after `setup_scheduler()`
3. **Dynamic access test**: `from app.tasks.scheduler import scheduler` returns the initialized instance
4. **Integration test**: Full startup sequence works correctly

## Deployment Checklist

Before deploying, ensure:

- [ ] All required environment variables are set in Render/deployment platform
- [ ] `SUPABASE_URL` is a valid Supabase URL
- [ ] `SUPABASE_KEY` is the service_role key (not anon key)
- [ ] `DISCORD_TOKEN` is valid and at least 50 characters
- [ ] `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI` are set
- [ ] `GROQ_API_KEY` starts with `gsk_`
- [ ] `JWT_SECRET` is at least 32 characters and randomly generated
- [ ] `CORS_ORIGINS` is set to your frontend URL
- [ ] `APP_ENV` is set to `prod` for production deployment

## Benefits

1. **No more crashes on startup**: Application starts even if configuration is incomplete
2. **Clear error messages**: Developers know exactly what's missing
3. **Backward compatible**: Existing test code continues to work
4. **Fail-fast in production**: Production deployments fail immediately with clear errors
5. **Better logging**: Comprehensive logs help debug initialization issues
