import pytest

from mood_diary.backend.utils.password_hasher import (
    PasswordHasher,
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


def test_password_hasher_verify_invalid_password_hash(
    password_hasher: PasswordHasher,
):
    password = "abcdefgh"

    assert not password_hasher.verify(password, "a$a")
    assert not password_hasher.verify(password, "abc")
