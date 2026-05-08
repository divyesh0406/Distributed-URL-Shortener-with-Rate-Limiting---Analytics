import hashlib
import string


ALPHABET = string.ascii_letters + string.digits
BASE = len(ALPHABET)
SHORT_CODE_LENGTH = 7


def _base62_encode(num: int) -> str:
    """Encode an integer as base62."""
    if num == 0:
        return ALPHABET[0]

    chars = []
    while num > 0:
        chars.append(ALPHABET[num % BASE])
        num //= BASE

    return "".join(reversed(chars))


def generate_short_code(long_url: str, idempotency_key: str = "") -> str:
    """
    Generate a deterministic short code for the URL and idempotency key.

    The same input always produces the same output, which lets later route
    handlers make duplicate shorten requests idempotent.
    """
    payload = f"{long_url}|{idempotency_key}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    num = int.from_bytes(digest[:7], "big")
    encoded = _base62_encode(num)

    return encoded[:SHORT_CODE_LENGTH].rjust(SHORT_CODE_LENGTH, ALPHABET[0])
