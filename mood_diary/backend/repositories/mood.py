from abc import abstractmethod
from uuid import UUID

from mood_diary.backend.repositories.base import BaseRepository
from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodType,
    UpdateMoodNote,
)

class MoodRepository(BaseRepository):
    @abstractmethod
    async def get(self, mood_id: UUID) -> MoodStamp | None:
        """Get user by ID. Returns None if user not found"""
        pass

    @abstractmethod
    async def create(self, body: CreateMoodStamp) -> MoodStamp | None:
        """Create new user. Returns None if user with the same username already exists"""
        pass

    @abstractmethod
    async def update_profile(
            self, mood_id: UUID, body: UpdateMoodType
    ) -> MoodStamp | None:
        """Update user profile by ID. Returns None if user not found"""
        pass

    @abstractmethod
    async def update_hashed_password(
            self, mood_id: UUID, body: UpdateMoodNote
    ) -> MoodStamp | None:
        """Update user hashed password by ID. Returns None if user not found"""
        pass
