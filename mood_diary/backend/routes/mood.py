from typing import List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, status, Path

from mood_diary.backend.routes.dependencies import (
    get_mood_service, get_current_user_id,
)
from mood_diary.backend.services.mood import MoodService
from mood_diary.common.api.schemas.mood import (

    CreateMoodStampRequest, GetMoodStampRequest, GetManyMoodStampsRequest, UpdateMoodStampRequest, MoodStampSchema)
from mood_diary.common.api.schemas.common import MessageResponse

router = APIRouter()


@router.post(
    "/moodstamp/",
    response_model=MoodStampSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": MoodStampSchema,
            "description": "MoodStamp recorded successfully",
        },
        400: {
            "model": MessageResponse,
            "description": "MoodStamp already exists",
            "content": {
                "application/json": {"example": {"message": "MoodStamp already exists"}}
            },
        },
    },
)
async def create(
        request: CreateMoodStampRequest,
        service: MoodService = Depends(get_mood_service)
):
    return await service.create(request)


@router.get(
    "/moodstamp/{date}",
    response_model=MoodStampSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": MoodStampSchema,
            "description": "MoodStamp retrieved successfully",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": MessageResponse,
            "description": "MoodStamp not found",
            "content": {
                "application/json": {"example": {"message": "MoodStamp does not exist"}}
            }
        },
    },
)
async def get_moodstamp(
        date: date = Path(...),
        user_id: UUID = Depends(get_current_user_id),
        service: MoodService = Depends(get_mood_service),
):
    request = GetMoodStampRequest(user_id=user_id, date=date)
    return await service.get(request)


@router.get(
    "/moodstamp/",
    response_model=List[MoodStampSchema],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": List[MoodStampSchema],
            "description": "MoodStamps retrieved successfully",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": MessageResponse,
            "description": "MoodStamps not found",
            "content": {
                "application/json": {"example": {"message": "MoodStamps does not exist"}}
            }
        },
    },
)
async def get_many_moodstamps(
        start_date: date,
        end_date: date,
        value: int | None = None,
        user_id: UUID = Depends(get_current_user_id),
        service: MoodService = Depends(get_mood_service),
):
    request = GetManyMoodStampsRequest(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        value=value,
    )
    return await service.get_many(request)


@router.put(
    "/moodstamp/{date}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "MoodStamp updated successfully"},
        status.HTTP_404_NOT_FOUND: {
            "model": MessageResponse,
            "description": "MoodStamp not found",
            "content": {
                "application/json": {"example": {"message": "MoodStamp does not exist"}}
            }
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": MessageResponse,
            "description": "Value/note are in the wrong format.",
            "content": {
                "application/json": {"example": {"message": "Value/note are in the wrong format."}}
            }
        }
    },
)
async def update_moodstamp(
        date: date = Path(...),
        request: UpdateMoodStampRequest = Depends(),
        user_id: UUID = Depends(get_current_user_id),
        service: MoodService = Depends(get_mood_service),
):
    request_data = UpdateMoodStampRequest(
        user_id=user_id,
        date=date,
        value=request.value,
        note=request.note,
    )
    return await service.update(request_data)


@router.delete(
    "/moodstamp/{date}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "MoodStamp deleted successfully"},
        status.HTTP_404_NOT_FOUND: {
            "model": MessageResponse,
            "description": "MoodStamp not found",
            "content": {
                "application/json": {"example": {"message": "MoodStamp does not exist"}}
            }
        },
    },
)
async def delete_moodstamp(
        date: date = Path(...),
        user_id: UUID = Depends(get_current_user_id),
        service: MoodService = Depends(get_mood_service),
):
    request = GetMoodStampRequest(user_id=user_id, date=date)
    return await service.delete(request)
