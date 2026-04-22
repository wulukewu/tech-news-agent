"""
Property-based tests for Data Security and Isolation (Property 14)

Feature: intelligent-qa-agent
Property 14: Data Security and Isolation

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

For any user query or conversation, the system SHALL:
1. Encrypt stored data (query logs and conversation data)
2. Enforce data retention policies (conversation expiry)
3. Ensure complete data isolation between users
4. Support complete data deletion on request
5. Never expose private information from other users
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from app.qa_agent.models import ConversationContext, ConversationStatus
from app.qa_agent.security_manager import EncryptionError, SecurityManager

# ============================================================================
# Custom Strategies for Test Data Generation
# ============================================================================


@composite
def nonempty_text(draw, min_size=1, max_size=500):
    """Generate non-empty text strings (ASCII + Unicode)."""
    return draw(
        st.text(
            alphabet=st.characters(
                blacklist_categories=("Cs",),  # exclude surrogates
            ),
            min_size=min_size,
            max_size=max_size,
        ).filter(lambda s: len(s) > 0)
    )


@composite
def json_serializable_dicts(draw):
    """Generate dictionaries with string keys and JSON-serializable values."""
    keys = draw(
        st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                min_size=1,
                max_size=20,
            ),
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    values = draw(
        st.lists(
            st.one_of(
                st.text(max_size=100),
                st.integers(min_value=-1000, max_value=1000),
                st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.none(),
            ),
            min_size=len(keys),
            max_size=len(keys),
        )
    )
    return dict(zip(keys, values))


@composite
def fernet_keys(draw):
    """Generate valid Fernet encryption keys."""
    # Fernet.generate_key() always produces a valid key; we just call it
    return Fernet.generate_key()


@composite
def past_datetimes(draw):
    """Generate datetimes in the past (at least 1 second ago)."""
    seconds_ago = draw(st.integers(min_value=1, max_value=365 * 24 * 3600))
    return datetime.utcnow() - timedelta(seconds=seconds_ago)


@composite
def future_datetimes(draw):
    """Generate datetimes in the future (at least 1 second ahead)."""
    seconds_ahead = draw(st.integers(min_value=1, max_value=365 * 24 * 3600))
    return datetime.utcnow() + timedelta(seconds=seconds_ahead)


@composite
def conversation_contexts(draw, expires_at=None):
    """Generate ConversationContext objects with optional expires_at."""
    user_id = uuid4()
    return ConversationContext(
        user_id=user_id,
        expires_at=expires_at,
        status=ConversationStatus.ACTIVE,
    )


# ============================================================================
# Shared SecurityManager (module-level, single key for encryption tests)
# ============================================================================

# A single SecurityManager instance is safe to share across Hypothesis examples
# because encrypt_text/decrypt_text/hash_sensitive_data are stateless pure methods.
_TEST_KEY = Fernet.generate_key()
_SHARED_SM = SecurityManager(encryption_key=_TEST_KEY)


# ============================================================================
# Property 14.1: Encryption Round-Trip
# **Validates: Requirement 10.1**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(plaintext=nonempty_text())
def test_property_14_1_encryption_roundtrip(plaintext):
    """
    Property 14.1: Encryption Round-Trip

    **Validates: Requirement 10.1**

    For any non-empty plaintext string, encrypt_text(plaintext) followed by
    decrypt_text(ciphertext) SHALL return the original plaintext. The ciphertext
    SHALL differ from the plaintext.
    """
    ciphertext = _SHARED_SM.encrypt_text(plaintext)

    # Ciphertext must differ from plaintext
    assert ciphertext != plaintext, "Ciphertext should differ from plaintext"

    # Round-trip must recover original plaintext
    recovered = _SHARED_SM.decrypt_text(ciphertext)
    assert recovered == plaintext, f"Round-trip failed: expected {plaintext!r}, got {recovered!r}"


# ============================================================================
# Property 14.2: Dictionary Encryption Round-Trip
# **Validates: Requirement 10.1**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(data=json_serializable_dicts())
def test_property_14_2_dict_encryption_roundtrip(data):
    """
    Property 14.2: Dictionary Encryption Round-Trip

    **Validates: Requirement 10.1**

    For any dictionary with string keys and JSON-serializable values,
    encrypt_dict(data) followed by decrypt_dict(ciphertext) SHALL return
    the original dictionary.
    """
    ciphertext = _SHARED_SM.encrypt_dict(data)

    # Ciphertext must be a non-empty string
    assert (
        isinstance(ciphertext, str) and len(ciphertext) > 0
    ), "encrypt_dict should return a non-empty string"

    # Round-trip must recover original dictionary
    recovered = _SHARED_SM.decrypt_dict(ciphertext)
    assert recovered == data, f"Dict round-trip failed: expected {data!r}, got {recovered!r}"


# ============================================================================
# Property 14.3: Encryption Produces Different Ciphertexts (Random IVs)
# **Validates: Requirement 10.1**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(plaintext=nonempty_text())
def test_property_14_3_encryption_random_iv(plaintext):
    """
    Property 14.3: Encryption Produces Different Ciphertexts

    **Validates: Requirement 10.1**

    For any plaintext, encrypting it twice SHALL produce different ciphertexts
    (Fernet uses random IVs), but both SHALL decrypt to the same plaintext.
    """
    ciphertext1 = _SHARED_SM.encrypt_text(plaintext)
    ciphertext2 = _SHARED_SM.encrypt_text(plaintext)

    # Two encryptions of the same plaintext must produce different ciphertexts
    assert ciphertext1 != ciphertext2, (
        "Two encryptions of the same plaintext should produce different ciphertexts "
        "(Fernet uses random IVs)"
    )

    # Both ciphertexts must decrypt to the original plaintext
    recovered1 = _SHARED_SM.decrypt_text(ciphertext1)
    recovered2 = _SHARED_SM.decrypt_text(ciphertext2)

    assert (
        recovered1 == plaintext
    ), f"First ciphertext did not decrypt correctly: expected {plaintext!r}, got {recovered1!r}"
    assert (
        recovered2 == plaintext
    ), f"Second ciphertext did not decrypt correctly: expected {plaintext!r}, got {recovered2!r}"


# ============================================================================
# Property 14.4: Empty String Handling
# **Validates: Requirement 10.1**
# ============================================================================


def test_property_14_4_empty_string_handling():
    """
    Property 14.4: Empty String Handling

    **Validates: Requirement 10.1**

    encrypt_text("") SHALL return "" and decrypt_text("") SHALL return ""
    without raising exceptions.
    """
    # encrypt_text("") must return "" without raising
    encrypted_empty = _SHARED_SM.encrypt_text("")
    assert encrypted_empty == "", f"encrypt_text('') should return '', got {encrypted_empty!r}"

    # decrypt_text("") must return "" without raising
    decrypted_empty = _SHARED_SM.decrypt_text("")
    assert decrypted_empty == "", f"decrypt_text('') should return '', got {decrypted_empty!r}"


# ============================================================================
# Property 14.5: Hash Determinism
# **Validates: Requirement 10.1**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    s=nonempty_text(),
    s2=nonempty_text(),
)
def test_property_14_5_hash_determinism(s, s2):
    """
    Property 14.5: Hash Determinism

    **Validates: Requirement 10.1**

    For any string, hash_sensitive_data(s) SHALL always return the same hash.
    For two different strings, the hashes SHALL differ (collision resistance
    for practical inputs).
    """
    # Same input always produces same hash
    hash1 = _SHARED_SM.hash_sensitive_data(s)
    hash2 = _SHARED_SM.hash_sensitive_data(s)
    assert hash1 == hash2, (
        f"hash_sensitive_data is not deterministic for input {s!r}: "
        f"got {hash1!r} then {hash2!r}"
    )

    # Different inputs should produce different hashes
    if s != s2:
        hash_s = _SHARED_SM.hash_sensitive_data(s)
        hash_s2 = _SHARED_SM.hash_sensitive_data(s2)
        assert hash_s != hash_s2, (
            f"Hash collision detected for different inputs {s!r} and {s2!r}: "
            f"both produced {hash_s!r}"
        )


# ============================================================================
# Property 14.6: Hash Is One-Way (SHA-256 Format)
# **Validates: Requirement 10.1**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(s=nonempty_text(min_size=1, max_size=200))
def test_property_14_6_hash_is_one_way(s):
    """
    Property 14.6: Hash Is One-Way

    **Validates: Requirement 10.1**

    The hash output SHALL be a 64-character hex string (SHA-256).
    The original plaintext SHALL NOT appear in the hash output.
    """
    hash_output = _SHARED_SM.hash_sensitive_data(s)

    # Must be a 64-character hex string (SHA-256 produces 32 bytes = 64 hex chars)
    assert isinstance(hash_output, str), "Hash output must be a string"
    assert (
        len(hash_output) == 64
    ), f"SHA-256 hash must be 64 hex characters, got {len(hash_output)}: {hash_output!r}"
    assert all(
        c in "0123456789abcdef" for c in hash_output
    ), f"Hash output must be lowercase hex, got: {hash_output!r}"

    # Original plaintext must not appear verbatim in the hash
    assert s not in hash_output, f"Plaintext {s!r} should not appear in hash output {hash_output!r}"


# ============================================================================
# Property 14.7: Conversation Expiry
# **Validates: Requirement 10.2**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(past_dt=past_datetimes(), future_dt=future_datetimes())
def test_property_14_7_conversation_expiry(past_dt, future_dt):
    """
    Property 14.7: Conversation Expiry

    **Validates: Requirement 10.2**

    For any ConversationContext with expires_at set to a past datetime,
    is_expired() SHALL return True. For expires_at set to a future datetime,
    is_expired() SHALL return False.
    """
    user_id = uuid4()

    # Expired conversation (expires_at in the past)
    expired_ctx = ConversationContext(
        user_id=user_id,
        expires_at=past_dt,
        status=ConversationStatus.ACTIVE,
    )
    assert (
        expired_ctx.is_expired() is True
    ), f"Conversation with expires_at={past_dt} (past) should be expired"

    # Active conversation (expires_at in the future)
    active_ctx = ConversationContext(
        user_id=user_id,
        expires_at=future_dt,
        status=ConversationStatus.ACTIVE,
    )
    assert (
        active_ctx.is_expired() is False
    ), f"Conversation with expires_at={future_dt} (future) should not be expired"


# ============================================================================
# Property 14.8: Conversation Active Status
# **Validates: Requirement 10.2**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    status=st.sampled_from(list(ConversationStatus)),
    use_past=st.booleans(),
)
def test_property_14_8_conversation_active_status(status, use_past):
    """
    Property 14.8: Conversation Active Status

    **Validates: Requirement 10.2**

    A conversation SHALL be active only when its status is ACTIVE and it has
    not expired.
    """
    user_id = uuid4()

    if use_past:
        expires_at = datetime.utcnow() - timedelta(seconds=10)
    else:
        expires_at = datetime.utcnow() + timedelta(seconds=3600)

    ctx = ConversationContext(
        user_id=user_id,
        expires_at=expires_at,
        status=status,
    )

    is_active = ctx.is_active()
    is_expired = ctx.is_expired()
    is_status_active = status == ConversationStatus.ACTIVE

    # is_active() must be True iff status==ACTIVE AND not expired
    expected_active = is_status_active and not is_expired
    assert is_active == expected_active, (
        f"is_active() should be {expected_active} for status={status}, "
        f"expired={is_expired}, but got {is_active}"
    )


# ============================================================================
# Property 14.9: User Data Isolation — Different Users Get Different IDs
# **Validates: Requirement 10.3**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    user_id_a=st.uuids(),
    user_id_b=st.uuids(),
)
def test_property_14_9_user_data_isolation_different_ids(user_id_a, user_id_b):
    """
    Property 14.9: User Data Isolation — Different Users Get Different Conversation IDs

    **Validates: Requirement 10.3**

    For any two different user UUIDs, conversations created for each user SHALL
    have different conversation IDs and SHALL NOT share context.
    """
    # Assume user_id_a != user_id_b (skip if equal — extremely rare with UUIDs)
    if user_id_a == user_id_b:
        return

    ctx_a = ConversationContext(user_id=user_id_a)
    ctx_b = ConversationContext(user_id=user_id_b)

    # Conversation IDs must be distinct
    assert (
        ctx_a.conversation_id != ctx_b.conversation_id
    ), "Two conversations for different users must have different conversation IDs"

    # Each context must reference its own user
    assert (
        ctx_a.user_id == user_id_a
    ), f"Context A should belong to user {user_id_a}, got {ctx_a.user_id}"
    assert (
        ctx_b.user_id == user_id_b
    ), f"Context B should belong to user {user_id_b}, got {ctx_b.user_id}"

    # Contexts must not share turns (both start empty)
    assert ctx_a.turns == [], "New conversation should have no turns"
    assert ctx_b.turns == [], "New conversation should have no turns"

    # Adding a turn to one context must not affect the other
    ctx_a.add_turn(query="What is AI?")
    assert len(ctx_a.turns) == 1, "Turn should be added to ctx_a"
    assert len(ctx_b.turns) == 0, "Adding a turn to ctx_a must not affect ctx_b (no shared state)"


# ============================================================================
# Property 14.10: Encryption Key Isolation
# **Validates: Requirement 10.3**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(plaintext=nonempty_text())
def test_property_14_10_encryption_key_isolation(plaintext):
    """
    Property 14.10: Encryption Key Isolation

    **Validates: Requirement 10.3**

    Two SecurityManager instances with different keys SHALL NOT be able to
    decrypt each other's ciphertext (raises EncryptionError).
    """
    key_a = Fernet.generate_key()
    key_b = Fernet.generate_key()

    # Ensure keys are different (astronomically unlikely to collide, but guard anyway)
    assert key_a != key_b, "Two independently generated Fernet keys must differ"

    manager_a = SecurityManager(encryption_key=key_a)
    manager_b = SecurityManager(encryption_key=key_b)

    # Encrypt with manager_a
    ciphertext_a = manager_a.encrypt_text(plaintext)

    # manager_b must NOT be able to decrypt manager_a's ciphertext
    with pytest.raises(EncryptionError):
        manager_b.decrypt_text(ciphertext_a)

    # Encrypt with manager_b
    ciphertext_b = manager_b.encrypt_text(plaintext)

    # manager_a must NOT be able to decrypt manager_b's ciphertext
    with pytest.raises(EncryptionError):
        manager_a.decrypt_text(ciphertext_b)
