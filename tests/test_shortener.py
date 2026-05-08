import string

from app.shortener import SHORT_CODE_LENGTH, generate_short_code


def test_consistent_hashing():
    a = generate_short_code("https://example.com", "key1")
    b = generate_short_code("https://example.com", "key1")

    assert a == b


def test_different_inputs_different_outputs():
    a = generate_short_code("https://example.com", "key1")
    b = generate_short_code("https://example.com", "key2")

    assert a != b


def test_short_code_length():
    code = generate_short_code("https://example.com")

    assert len(code) == SHORT_CODE_LENGTH


def test_alphanumeric_only():
    code = generate_short_code("https://example.com")

    assert all(char in string.ascii_letters + string.digits for char in code)
