# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Oversized Draft Crashes followup.send
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to drafts where len(draft) > 2000 (isBugCondition = True)
  - Test that followup.send is called with len(content) > 2000 on unfixed code (from Bug Condition in design)
  - The test assertions should match the Expected Behavior: every followup.send call receives <= 2000 chars
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., followup.send called with 2001-char string, causing HTTP 400)
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Short Draft Sent Unmodified
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: followup.send(content=draft, view=view) is called unmodified when len(draft) <= 2000
  - Write property-based test: for all draft strings where len(draft) <= 2000, content sent equals draft exactly
  - Verify test passes on UNFIXED code (confirms baseline behavior to preserve)
  - _Requirements: 3.1, 3.2_

- [x] 3. Fix for oversized draft crashing Discord followup.send
  - [x] 3.1 Implement the truncation guard in news_commands.py
    - After `draft = await llm.generate_weekly_newsletter(hardcore_articles)`, add length check
    - If `len(draft) > 2000`, set `draft = draft[:1997] + "..."`
    - Replace misleading comment "We enforce 3500 max in the LLM prompt" with accurate note
    - _Bug_Condition: isBugCondition(draft) where len(draft) > 2000_
    - _Expected_Behavior: every followup.send call receives content with len <= 2000_
    - _Preservation: drafts <= 2000 chars are sent unmodified; view=view always attached to first send_
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Oversized Draft Is Safely Delivered
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Short Draft Behavior Is Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
