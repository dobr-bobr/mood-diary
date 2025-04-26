from typing import List

from mood_diary.backend.exceptions.mood import MoodStampAlreadyExist, MoodStampNotExist
from mood_diary.backend.repositories.mood import MoodStampRepository
from mood_diary.backend.repositories.sсhemas.mood import MoodStamp, CreateMoodStamp, UpdateMoodStamp, MoodStampFilter
from mood_diary.common.api.schemas.mood import CreateMoodStampRequest, UpdateMoodStampRequest, GetMoodStampRequest, \
    GetManyMoodStampsRequest


class MoodService:
    def __init__(self, moodstamp_repository: MoodStampRepository):
        self.moodstamp_repository = moodstamp_repository

    async def create(self, body: CreateMoodStampRequest) -> MoodStamp:
        create_moodstamp = CreateMoodStamp(
            date=body.date,
            user_id=body.user_id,
            value=body.value,
            note=body.note,
        )

        moodstamp = await self.moodstamp_repository.create(create_moodstamp)

        if moodstamp is None:
            raise MoodStampAlreadyExist()

        return MoodStamp(
            id=moodstamp.id,
            date=moodstamp.date,
            user_id=moodstamp.user_id,
            value=moodstamp.value,
            note=moodstamp.note,
            created_at=moodstamp.created_at,
            updated_at=moodstamp.updated_at,
        )

    async def get(self, body: GetMoodStampRequest) -> MoodStamp:
        moodstamp = await self.moodstamp_repository.get(
            user_id=body.user_id,
            date=body.date
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

    async def update(self, body: UpdateMoodStampRequest) -> MoodStamp:
        update_moodstamp = UpdateMoodStamp(
            user_id=body.user_id,
            value=body.value,
            note=body.note,
        )

        moodstamp = await self.moodstamp_repository.update(user_id=update_moodstamp.user_id,
                                                           date=body.date,
                                                           body=update_moodstamp)

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

    async def get_many(self, body: GetManyMoodStampsRequest) -> List[MoodStamp]:
        filter = MoodStampFilter(
            user_id=body.user_id,
            start_date=body.start_date,
            end_date=body.end_date,
            value=body.value,
        )

        moodstamps = await self.moodstamp_repository.get_many(
            body=filter,
        )

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

    async def delete(self, body: GetMoodStampRequest) -> None:
        success = await self.moodstamp_repository.delete(
            user_id=body.user_id,
            date=body.date,
        )

        if not success:
            raise MoodStampNotExist()
