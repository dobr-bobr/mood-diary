import pytest

from mood_diary.backend.utils.password_hasher import (
    PasswordHasher,
    SaltPasswordHasher,
)
from mood_diary.backend.utils.token_manager import (
    TokenManager,
    JWTTokenManager,
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


@pytest.fixture
def token_manager() -> TokenManager:
    return JWTTokenManager(
        secret_key="kl3hj2rkf3ht45kj1bg2lk45gkl2dhg4kjl5as232we24fdd",
        algorithm="HS256",
        access_token_exp_minutes=5,
        refresh_token_exp_minutes=30,
    )
