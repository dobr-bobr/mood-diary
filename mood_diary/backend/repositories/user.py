from abc import abstractmethod
from uuid import UUID

from mood_diary.backend.repositories.base import BaseRepository
from mood_diary.backend.repositories.sсhemas.user import (
    User,
    CreateUser,
    UpdateUserProfile,
    UpdateUserHashedPassword,
)


class UserRepository(BaseRepository):
    @abstractmethod
    async def get(self, user_id: UUID) -> User | None:
        """
        Get user by ID.
        Returns None if user not found.
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """
        Get user by username.
        Returns None if user not found.
        """
        pass

    @abstractmethod
    async def create(self, body: CreateUser) -> User | None:
        """
        Create new user.
        Returns None if user with the same username already exists.
        """
        pass

    @abstractmethod
    async def update_profile(
        self, user_id: UUID, body: UpdateUserProfile
    ) -> User | None:
        """
        Update user profile by ID.
        Returns None if user not found.
        """
        pass

    @abstractmethod
    async def update_hashed_password(
        self, user_id: UUID, body: UpdateUserHashedPassword
    ) -> User | None:
        """
        Update user hashed password by ID.
        Returns None if user not found.
        """
        pass
