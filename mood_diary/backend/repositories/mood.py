from abc import abstractmethod
from datetime import date

from mood_diary.backend.repositories.base import BaseRepository
from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodStamp
)

class MoodRepository(BaseRepository):
    @abstractmethod
    async def get(self, entry_date: date) -> MoodStamp | None:
        """Get moodstamp by entry date. Returns None if stamp not found"""
        pass

    @abstractmethod
    async def create(self, body: CreateMoodStamp) -> MoodStamp | None:
        """Create new moodstamp. Returns None if moodstamp with the same entry date already exists"""
        pass

    @abstractmethod
    async def update(
            self, entry_date: date, body: UpdateMoodStamp
    ) -> MoodStamp | None:
        """Update moodstamp by date. Returns None if moodstamp not found"""
        pass

    @abstractmethod
    async def delete(self, entry_date: date) -> MoodStamp | None:
        """Delete moodstamp by date. Returns None if stamp not found"""
        pass
