import hashlib
import os
import secrets
from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a password"""
        pass

    @abstractmethod
    def verify(self, password: str, stored_hash: str) -> bool:
        """Verify a password against a stored hash"""
        pass


class SaltPasswordHasher(PasswordHasher):
    def __init__(
        self,
        encoding: str,
        salt_size: int,
        hash_name: str,
        hash_iterations: int,
        split_char: str,
    ):
        self.encoding = encoding
        self.salt_size = salt_size
        self.hash_name = hash_name
        self.hash_iterations = hash_iterations
        self.split_char = split_char

    def hash(self, password: str) -> str:
        salt = os.urandom(self.salt_size)

        password_bytes = self.__password_bytes(password)
        password_hash = self.__password_hash(password_bytes, salt)

        return f"{salt.hex()}{self.split_char}{password_hash.hex()}"

    def verify(self, password: str, stored_hash: str) -> bool:
        try:
            salt, expected_password_hash = [
                bytes.fromhex(x) for x in stored_hash.split(self.split_char)
            ]
        except ValueError:
            return False

        password_bytes = self.__password_bytes(password)
        password_hash = self.__password_hash(password_bytes, salt)

        return secrets.compare_digest(password_hash, expected_password_hash)

    def __password_hash(self, password_bytes: bytes, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            self.hash_name, password_bytes, salt, self.hash_iterations
        )

    def __password_bytes(self, password: str | bytes) -> bytes:
        if isinstance(password, str):
            return password.encode(self.encoding)
        elif isinstance(password, bytes):
            return password
        else:
            raise TypeError("Password must be str or bytes")
