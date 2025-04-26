from abc import abstractmethod
from datetime import date

from uuid import UUID

from mood_diary.backend.repositories.base import BaseRepository
from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodStamp,
    MoodStampFilter
)


class MoodStampRepository(BaseRepository):
    @abstractmethod
    async def get(self, date: date, user_id: UUID) -> MoodStamp | None:
        """
        Get moodstamp by entry date.
        Returns None if stamp not found
        """
        pass

    @abstractmethod
    async def get_many(self, body: MoodStampFilter) -> list[MoodStamp] | None:
        """
        Get multiple moodstamps based on filter criteria.
        Returns empty list if no stamps found
        """
        pass

    @abstractmethod
    async def create(self, body: CreateMoodStamp) -> MoodStamp | None:
        """
        Create new moodstamp.
        Returns None if moodstamp with the same entry date already exists
        """
        pass

    @abstractmethod
    async def update(
            self, date: date, user_id: UUID, body: UpdateMoodStamp
    ) -> MoodStamp | None:
        """
        Update moodstamp by date.
        Returns None if moodstamp not found
        """
        pass

    @abstractmethod
    async def delete(self, date: date, user_id: UUID) -> MoodStamp | None:
        """
        Delete moodstamp by date.
        Returns None if moodstamp not found
        """
        pass
