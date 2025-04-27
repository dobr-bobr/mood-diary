import pytest

from mood_diary.backend.utils.password_hasher import (
    PasswordHasher,
    SaltPasswordHasher,
)


@pytest.fixture
def password_hasher() -> PasswordHasher:
    return SaltPasswordHasher(
        encoding="utf-8",
        hash_name="sha256",
        hash_iterations=100000,
        salt_size=16,
        split_char="$",
    )


def test_password_hasher(password_hasher: PasswordHasher):
    password = "abcdefgh"
    password_hash = password_hasher.hash(password)
    assert password_hasher.verify(password, password_hash)


def test_password_hasher_same_password(password_hasher: PasswordHasher):
    password = "abcdefgh"
    password_hash1 = password_hasher.hash(password)
    password_hash2 = password_hasher.hash(password)
    assert password_hash1 != password_hash2


def test_verify_failure(password_hasher: SaltPasswordHasher):
    password = "mysecretpassword"
    wrong_password = "anotherpassword"
    hashed = password_hasher.hash(password)
    result = password_hasher.verify(wrong_password, hashed)
    assert result is False


def test_verify_invalid_hash_format_split(password_hasher: SaltPasswordHasher):
    """Test verify with a hash string that doesn't contain the split char."""
    password = "mysecretpassword"
    invalid_hash = "justhexstringwithoutsplitchar"
    result = password_hasher.verify(password, invalid_hash)
    assert result is False


def test_verify_invalid_hash_format_hex(password_hasher: SaltPasswordHasher):
    """Test verify with a hash string containing non-hex characters."""
    password = "mysecretpassword"
    split_char = password_hasher.split_char
    invalid_hash = f"validhex{split_char}invalidhexZ"
    result = password_hasher.verify(password, invalid_hash)
    assert result is False


def test_hash_bytes_input(password_hasher: SaltPasswordHasher):
    """Test hashing bytes directly."""
    password_bytes = b"mysecretbytespassword"
    hashed = password_hasher.hash(password_bytes)  # type: ignore # Test bytes input directly
    assert isinstance(hashed, str)
    assert password_hasher.split_char in hashed
    # Verify the bytes password
    result = password_hasher.verify(password_bytes, hashed)
    assert result is True


def test_verify_bytes_password_input(password_hasher: SaltPasswordHasher):
    """Test verifying with bytes password input."""
    password = "mysecretpassword"
    password_bytes = password.encode(password_hasher.encoding)
    hashed = password_hasher.hash(password)
    result = password_hasher.verify(password_bytes, hashed)  # type: ignore # Test bytes input directly
    assert result is True


def test_invalid_password_type(password_hasher: SaltPasswordHasher):
    """Test that hashing raises TypeError for invalid password types."""
    with pytest.raises(TypeError, match="Password must be str or bytes"):
        password_hasher.hash(12345)  # type: ignore
