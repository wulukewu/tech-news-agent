# Translation Validation Pre-Commit Hook

## Overview

The translation validation pre-commit hook automatically checks translation completeness before allowing commits that modify translation files. This ensures that all supported languages remain synchronized and complete.

## What It Does

The hook runs automatically when you commit changes to translation files (`frontend/locales/*.json`) and validates:

1. **Key Completeness**: All translation keys exist in both `en-US.json` and `zh-TW.json`
2. **No Empty Values**: All translation values are filled in (not empty, null, or undefined)
3. **Structure Consistency**: Nested object structures match across language files

## How It Works

### Automatic Validation

When you commit changes to translation files:

```bash
git add frontend/locales/en-US.json
git commit -m "Add new translation keys"
```

The hook automatically runs and:

- ✅ **Allows commit** if all translations are complete
- ❌ **Blocks commit** if translations are incomplete or have empty values

### Manual Validation

You can run the validation manually at any time:

```bash
# From project root
cd frontend && npm run find:missing-translations

# Or using pre-commit
pre-commit run validate-translations --all-files
```

## Example Output

### ✅ Success (All Translations Complete)

```
Translation Completeness Report

Total keys in zh-TW.json: 166
Total keys in en-US.json: 166

✓ All translations are complete!
```

### ❌ Failure (Missing or Empty Translations)

```
Translation Completeness Report

Total keys in zh-TW.json: 165
Total keys in en-US.json: 166

✗ Found 2 translation issue(s)

Missing in zh-TW.json (1):
  ✗ buttons.new-button
    en-US value: "New Button"

Empty values in en-US.json (1):
  ⚠ messages.new-message
    zh-TW value: "新訊息"

Summary:
  Missing keys: 1
  Empty values: 1
```

## Common Scenarios

### Adding a New Translation Key

When adding a new key, you must add it to **both** language files:

```json
// frontend/locales/en-US.json
{
  "buttons": {
    "new-action": "New Action"  // ← Add here
  }
}

// frontend/locales/zh-TW.json
{
  "buttons": {
    "new-action": "新動作"  // ← And here
  }
}
```

### Fixing Missing Translations

If the hook reports missing keys:

1. Check the output to see which keys are missing
2. Add the missing keys to the appropriate file
3. Ensure the nested structure matches
4. Try committing again

### Fixing Empty Values

If the hook reports empty values:

1. Find the keys with empty values
2. Fill in the translation text
3. Try committing again

## Troubleshooting

### Hook Blocks My Commit

**Problem**: The hook prevents you from committing translation changes.

**Solution**:

1. Read the error output carefully
2. Fix the reported issues (missing keys or empty values)
3. Run `npm run find:missing-translations` to verify
4. Try committing again

### I Need to Commit Incomplete Translations

**Problem**: You're working on translations incrementally and need to commit partial work.

**Solution**: This is intentionally not allowed to prevent incomplete translations from reaching production. Instead:

1. Complete all translations before committing
2. Or work in a separate branch and merge when complete
3. Or use git stash to temporarily save incomplete work

**Emergency bypass** (not recommended):

```bash
git commit --no-verify -m "WIP: incomplete translations"
```

### Hook Doesn't Run

**Problem**: The hook doesn't run when committing translation files.

**Solution**:

1. Ensure pre-commit is installed: `pre-commit install`
2. Check if `.pre-commit-config.yaml` exists
3. Try running manually: `pre-commit run validate-translations --all-files`

### False Positives

**Problem**: The hook reports issues that don't exist.

**Solution**:

1. Verify JSON syntax is valid (no trailing commas, proper quotes)
2. Check for hidden characters or encoding issues
3. Ensure nested structure matches exactly across files

## Configuration

### Hook Configuration

The hook is configured in `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: validate-translations
      name: Validate translations completeness
      entry: bash -c 'cd frontend && npm run find:missing-translations'
      language: system
      files: ^frontend/locales/.*\.json$
      pass_filenames: false
```

### Script Location

The validation script is located at:

```
frontend/scripts/find-missing-translations.js
```

### Supported Languages

Currently validates:

- `en-US.json` (English)
- `zh-TW.json` (Traditional Chinese)

## Best Practices

### 1. Add Translations Together

Always add new keys to both language files in the same commit:

```bash
# Edit both files
vim frontend/locales/en-US.json
vim frontend/locales/zh-TW.json

# Commit together
git add frontend/locales/*.json
git commit -m "Add new translation keys for feature X"
```

### 2. Use Descriptive Keys

Use clear, hierarchical keys that describe the content:

```json
{
  "buttons": {
    "save": "Save",
    "cancel": "Cancel"
  },
  "messages": {
    "save-success": "Saved successfully"
  }
}
```

### 3. Maintain Structure Consistency

Keep the same nested structure across all language files:

```json
// ✅ Good - Same structure
// en-US.json
{ "nav": { "home": "Home" } }

// zh-TW.json
{ "nav": { "home": "首頁" } }

// ❌ Bad - Different structure
// en-US.json
{ "nav": { "home": "Home" } }

// zh-TW.json
{ "navigation": { "home": "首頁" } }
```

### 4. Test Before Committing

Run validation manually before committing:

```bash
npm run find:missing-translations
```

### 5. Keep Translations Up-to-Date

When modifying existing translations:

- Update both language files
- Verify the meaning is preserved
- Check for context-specific translations

## Related Documentation

- [i18n Developer Guide](./i18n-guide.md) - Complete guide to using the bilingual UI system
- [Pre-commit Hooks](./PRE_COMMIT_HOOKS.md) - All pre-commit hooks documentation
- [ESLint I18n Rules](./eslint-i18n-rules.md) - ESLint rules to prevent hardcoded text

## Requirements

This hook validates:

- **Requirement 11.5**: Translation validation prevents commits with incomplete translations

## Exit Codes

- `0`: All translations are complete (commit allowed)
- `1`: Missing or empty translations found (commit blocked)

---

**Last Updated**: January 2025
