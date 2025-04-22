import pytest

from mood_diary.backend.utils.password_hasher import (
    SaltPasswordHasher,
    PasswordHasher,
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
