# Discord Message Length Fix - Bugfix Design

## Overview

The `/news_now` command crashes with `discord.errors.HTTPException: 400 Bad Request` when the LLM-generated newsletter draft exceeds Discord's hard 2000-character limit for message content. The fix adds a truncation/splitting guard in `news_commands.py` before calling `interaction.followup.send`, ensuring the content is always within Discord's limit regardless of what the LLM returns. The LLM prompt instruction (3500 char soft limit) is unreliable and cannot be the sole safeguard.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when `len(draft) > 2000` at the point of calling `interaction.followup.send(content=draft, ...)`
- **Property (P)**: The desired behavior when the bug condition holds — the content is truncated or split so every `followup.send` call receives a string of 2000 characters or fewer
- **Preservation**: Existing behavior for drafts ≤ 2000 characters, button view attachment, and all other error paths that must remain unchanged
- **`generate_weekly_newsletter`**: The method in `app/services/llm_service.py` that calls the LLM and returns the raw draft string
- **`news_now`**: The slash command handler in `app/bot/cogs/news_commands.py` that calls `generate_weekly_newsletter` and sends the result to Discord
- **Discord message limit**: Discord's hard limit of 2000 characters for the `content` field of a regular message sent via `followup.send`

## Bug Details

### Bug Condition

The bug manifests when `generate_weekly_newsletter()` returns a string longer than 2000 characters. The `news_now` handler passes this string directly to `interaction.followup.send(content=draft, ...)` without any length check, causing Discord's API to reject the request with HTTP 400.

**Formal Specification:**

```
FUNCTION isBugCondition(draft)
  INPUT: draft of type str (LLM-generated newsletter content)
  OUTPUT: boolean

  RETURN len(draft) > 2000
END FUNCTION
```

### Examples

- Draft is 2450 characters → `followup.send` raises `HTTPException: 400 Bad Request`, user sees no response
- Draft is 3100 characters (LLM ignored the 3500-char prompt instruction) → same crash
- Draft is 1999 characters → sends successfully, no bug
- Draft is exactly 2000 characters → sends successfully, no bug (boundary, not buggy)
- Draft is 2001 characters → bug condition holds, crash occurs

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- When `len(draft) <= 2000`, the message is sent in a single `followup.send` call without any modification to the content
- The `ReadLaterView` (with "稍後閱讀" buttons) is always attached to the first `followup.send` call
- All other error paths (`no feeds`, `no articles`, `LLM failure`) continue to return their existing informational or error messages unchanged

**Scope:**
All inputs where `len(draft) <= 2000` must be completely unaffected by this fix. This includes:

- Short drafts (e.g., "本週沒有足夠硬核的技術資訊 🥲")
- Drafts that happen to be exactly at the limit
- All non-draft error responses sent via `followup.send`

## Hypothesized Root Cause

Based on the bug description and code review:

1. **Missing length guard before send**: `news_commands.py` line 53 passes `draft` directly to `followup.send` with no `len(draft)` check. This is the primary cause.

2. **Unreliable soft limit in LLM prompt**: `llm_service.py` instructs the model to stay under 3500 characters, but LLMs do not reliably honor character-count instructions. The `max_tokens=2000` setting limits tokens, not characters — a token can be less than one character, so 2000 tokens can easily exceed 2000 characters.

3. **Incorrect comment in source**: The comment on line 51 of `news_commands.py` states "We enforce 3500 max in the LLM prompt" — this is misleading; it is a request, not an enforcement.

4. **No post-generation sanitization**: There is no post-processing step between `generate_weekly_newsletter()` returning and the content being sent to Discord.

## Correctness Properties

Property 1: Bug Condition - Oversized Draft Is Safely Delivered

_For any_ draft string where `isBugCondition(draft)` is true (i.e., `len(draft) > 2000`), the fixed `news_now` handler SHALL send the content to Discord without raising `HTTPException`, by ensuring every individual `followup.send` call receives a content string of 2000 characters or fewer.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Short Draft Behavior Is Unchanged

_For any_ draft string where `isBugCondition(draft)` is false (i.e., `len(draft) <= 2000`), the fixed `news_now` handler SHALL send the message in a single `followup.send` call with the content unmodified, preserving identical behavior to the original code.

**Validates: Requirements 3.1, 3.2**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `app/bot/cogs/news_commands.py`

**Function**: `news_now`

**Specific Changes**:

1. **Add a truncation helper**: After receiving `draft` from `llm.generate_weekly_newsletter(hardcore_articles)`, apply a length guard before calling `followup.send`.

2. **Truncation strategy**: Truncate the draft to 1997 characters and append `"..."` if `len(draft) > 2000`. This is the minimal, safe approach that avoids splitting mid-word and keeps the fix localized to the call site.

3. **Preserve view attachment**: The `view=view` argument must remain on the (first) `followup.send` call regardless of whether truncation occurred.

4. **Update misleading comment**: Replace the comment "We enforce 3500 max in the LLM prompt" with an accurate note explaining the hard enforcement now happens at send time.

5. **Optional — fix LLM prompt**: Update the system prompt in `llm_service.py` to target 1800 characters (not 3500) to reduce truncation frequency, but this is a secondary improvement and not the primary fix.

**Pseudocode for the fix:**

```
DISCORD_LIMIT = 2000
TRUNCATION_SUFFIX = "..."

draft = await llm.generate_weekly_newsletter(hardcore_articles)

IF len(draft) > DISCORD_LIMIT THEN
  draft = draft[:DISCORD_LIMIT - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX
END IF

await interaction.followup.send(content=draft, view=view)
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis.

**Test Plan**: Write unit tests that call the send logic with a draft string longer than 2000 characters and assert that `HTTPException` is raised (or that the mock `followup.send` is called with an oversized string). Run these tests on the UNFIXED code to observe failures.

**Test Cases**:

1. **2001-char draft test**: Pass a 2001-character string as `draft` and assert `followup.send` is called with `len(content) > 2000` (will demonstrate the bug on unfixed code)
2. **3500-char draft test**: Pass a 3500-character string (the LLM's supposed max) and assert the same (will demonstrate the bug on unfixed code)
3. **Exact boundary test**: Pass a 2000-character string and assert it sends without error (should pass even on unfixed code — confirms boundary)
4. **Unicode/emoji draft test**: Pass a 2001-character string containing multi-byte emoji characters and assert the bug condition holds (may reveal off-by-one issues with character counting)

**Expected Counterexamples**:

- `followup.send` is called with `len(content) > 2000`, which would cause Discord API to return HTTP 400
- Possible causes: no length check at call site, LLM ignoring token/character limits

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**

```
FOR ALL draft WHERE isBugCondition(draft) DO
  result_content := apply_fix(draft)
  ASSERT len(result_content) <= 2000
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**

```
FOR ALL draft WHERE NOT isBugCondition(draft) DO
  ASSERT send_original(draft) == send_fixed(draft)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:

- It generates many string lengths automatically (0 to 2000 chars) across the input domain
- It catches edge cases like empty strings, exactly-2000-char strings, and strings with multi-byte characters
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe that short drafts send unmodified on unfixed code, then write property-based tests to verify this continues after the fix.

**Test Cases**:

1. **Short draft preservation**: Verify drafts ≤ 2000 chars are sent unmodified (content identical, single send call)
2. **View attachment preservation**: Verify `view=view` is always passed to the first `followup.send` call regardless of draft length
3. **Error path preservation**: Verify "no feeds", "no articles", and LLM exception paths are unaffected by the fix

### Unit Tests

- Test that a 2001-char draft is truncated to exactly 2000 chars with `"..."` suffix
- Test that a 2000-char draft is sent unmodified
- Test that a 1-char draft is sent unmodified
- Test that the `ReadLaterView` is attached to the send call after truncation

### Property-Based Tests

- Generate random strings of length 1–4000 and verify the post-fix content sent to Discord always has `len <= 2000`
- Generate random strings of length 1–2000 and verify the content is sent unmodified (identical to input)
- Generate random strings with emoji/unicode and verify character counting is correct

### Integration Tests

- Test the full `/news_now` flow with a mocked LLM returning a 3000-char draft — verify the message is delivered successfully
- Test the full `/news_now` flow with a mocked LLM returning a 500-char draft — verify the message is delivered unmodified
- Test that "稍後閱讀" buttons appear on the response message in both truncated and non-truncated cases
