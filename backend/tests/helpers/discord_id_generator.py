"""
Helper utilities for generating valid Discord IDs in tests.

Discord IDs are snowflake IDs - 64-bit integers represented as strings.
They must be numeric and within the valid range.
"""

import random
from datetime import datetime


def generate_test_discord_id() -> str:
    """
    Generate a valid test Discord ID (snowflake format).

    Discord snowflakes are 64-bit integers with the following structure:
    - Bits 63-22: Timestamp (milliseconds since Discord epoch: 2015-01-01)
    - Bits 21-17: Internal worker ID
    - Bits 16-12: Internal process ID
    - Bits 11-0: Increment

    For testing, we generate a simple valid snowflake in the valid range.

    Returns:
        A valid Discord ID as a numeric string
    """
    # Discord epoch: January 1, 2015 00:00:00 UTC
    DISCORD_EPOCH = 1420070400000

    # Current timestamp in milliseconds since Discord epoch
    now_ms = int(datetime.utcnow().timestamp() * 1000)
    timestamp = now_ms - DISCORD_EPOCH

    # Generate random worker, process, and increment values
    worker_id = random.randint(0, 31)  # 5 bits
    process_id = random.randint(0, 31)  # 5 bits
    increment = random.randint(0, 4095)  # 12 bits

    # Construct snowflake
    snowflake = (timestamp << 22) | (worker_id << 17) | (process_id << 12) | increment

    # Ensure it's within valid range (max 64-bit signed int)
    snowflake = min(snowflake, 9223372036854775807)

    return str(snowflake)


def generate_test_discord_ids(count: int) -> list[str]:
    """
    Generate multiple unique test Discord IDs.

    Args:
        count: Number of Discord IDs to generate

    Returns:
        List of unique Discord IDs as numeric strings
    """
    ids = set()
    while len(ids) < count:
        ids.add(generate_test_discord_id())
    return list(ids)


# For backward compatibility with existing tests
def generate_numeric_discord_id() -> str:
    """
    Generate a simple numeric Discord ID for testing.

    This is a simpler alternative that generates a random number
    in the valid Discord ID range.

    Returns:
        A valid Discord ID as a numeric string
    """
    # Generate a random number in a safe range
    # Using a range that's clearly in the valid Discord ID space
    min_id = 100000000000000000  # ~18 digits
    max_id = 999999999999999999  # ~18 digits (well below max)

    return str(random.randint(min_id, max_id))
