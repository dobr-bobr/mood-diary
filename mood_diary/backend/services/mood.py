from uuid import UUID
from datetime import date

from mood_diary.backend.exceptions.mood import (
    MoodStampAlreadyExists,
    MoodStampNotExist,
    MoodStampAlreadyExistsErrorRepo,
)
from mood_diary.backend.repositories.mood import MoodStampRepository
from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodStamp,
    MoodStampFilter,
)
from mood_diary.common.api.schemas.mood import (
    CreateMoodStampRequest,
    UpdateMoodStampRequest,
    GetManyMoodStampsRequest,
)


class MoodService:
    def __init__(self, moodstamp_repository: MoodStampRepository):
        self.moodstamp_repository = moodstamp_repository

    async def create(
            self, user_id: UUID, body: CreateMoodStampRequest
    ) -> MoodStamp:
        create_moodstamp = CreateMoodStamp(
            user_id=user_id,
            date=body.date,
            value=body.value,
            note=body.note,
        )

        try:
            moodstamp = await self.moodstamp_repository.create(
                user_id=user_id, body=create_moodstamp
            )
        except MoodStampAlreadyExistsErrorRepo:
            raise MoodStampAlreadyExists()

        return MoodStamp(
            id=moodstamp.id,
            date=moodstamp.date,
            user_id=moodstamp.user_id,
            value=moodstamp.value,
            note=moodstamp.note,
            created_at=moodstamp.created_at,
            updated_at=moodstamp.updated_at,
        )

    async def get(self, user_id: UUID, date: date) -> MoodStamp:
        moodstamp = await self.moodstamp_repository.get(
            user_id=user_id, date=date
        )

        if moodstamp is None:
            raise MoodStampNotExist()

        return MoodStamp(
            id=moodstamp.id,
            date=moodstamp.date,
            user_id=moodstamp.user_id,
            value=moodstamp.value,
            note=moodstamp.note,
            created_at=moodstamp.created_at,
            updated_at=moodstamp.updated_at,
        )

    async def update(
            self, user_id: UUID, date: date, body: UpdateMoodStampRequest
    ) -> MoodStamp:
        update_moodstamp = UpdateMoodStamp(
            value=body.value,
            note=body.note,
        )

        moodstamp = await self.moodstamp_repository.update(
            user_id=user_id,
            date=date,
            body=update_moodstamp,
        )

        if moodstamp is None:
            raise MoodStampNotExist()

        return MoodStamp(
            id=moodstamp.id,
            date=moodstamp.date,
            user_id=moodstamp.user_id,
            value=moodstamp.value,
            note=moodstamp.note,
            created_at=moodstamp.created_at,
            updated_at=moodstamp.updated_at,
        )

    async def get_many(
            self, user_id: UUID, body: GetManyMoodStampsRequest
    ) -> list[MoodStamp]:
        filter = MoodStampFilter(
            start_date=body.start_date,
            end_date=body.end_date,
            value=body.value,
        )

        moodstamps = await self.moodstamp_repository.get_many(
            user_id=user_id,
            body=filter,
        )

        if moodstamps is None:
            return []

        return [
            MoodStamp(
                id=moodstamp.id,
                date=moodstamp.date,
                user_id=moodstamp.user_id,
                value=moodstamp.value,
                note=moodstamp.note,
                created_at=moodstamp.created_at,
                updated_at=moodstamp.updated_at,
            )
            for moodstamp in moodstamps
        ]

    async def delete(self, user_id: UUID, date: date) -> None:
        success = await self.moodstamp_repository.delete(
            user_id=user_id,
            date=date,
        )

        if not success:
            raise MoodStampNotExist()
