from typing import List
from uuid import UUID

from fastapi import APIRouter, Response, Depends, status
from google.protobuf import service

from mood_diary.backend.repositories.sсhemas.mood import MoodStamp, CreateMoodStamp
from mood_diary.backend.routes.dependencies import (
    get_current_user_id,
    get_mood_service,
)
from mood_diary.backend.services.mood import MoodService
from mood_diary.backend.services.user import UserService
from mood_diary.common.api.schemas.mood import (

    CreateMoodStampRequest, GetMoodStampRequest, GetManyMoodStampsRequest, UpdateMoodStampRequest)
from mood_diary.common.api.schemas.common import MessageResponse

router = APIRouter()


@router.post(
    "/moodstamp/",
    response_model=MoodStamp,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": MoodStamp,
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
    response_model=MoodStamp,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": MoodStamp,
            "description": "MoodStamp retrieved successfully",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponse,
            "description": "Invalid or expired token",
            "content": {
                "application/json": {"example": {"message": "Invalid or expired token"}}
            },
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
        request: GetMoodStampRequest,
        service: MoodService = Depends(get_mood_service),
):
    return await service.get(request)


@router.get(
    "/moodstamp?start=&end=&value=",
    response_model=List[MoodStamp],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": List[MoodStamp],
            "description": "MoodStamps retrieved successfully",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponse,
            "description": "Invalid or expired token",
            "content": {
                "application/json": {"example": {"message": "Invalid or expired token"}}
            },
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
        request: GetManyMoodStampsRequest,
        service: MoodService = Depends(get_mood_service),
):
    return await service.get_many(request)


@router.put(
    "/moodstamp/{date}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Password changed successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponse,
            "description": "Incorrect old password",
            "content": {
                "application/json": {"example": {"message": "Incorrect old password"}}
            },
        },
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
        request: UpdateMoodStampRequest,
        service: MoodService = Depends(get_mood_service),
):
    return await service.update(request)


@router.delete(
    "/moodstamp/{date}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "MoodStamp deleted successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponse,
            "description": "Incorrect old password",
            "content": {
                "application/json": {"example": {"message": "Incorrect old password"}}
            },
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
async def delete_moodstamp(
        request: GetMoodStampRequest,
        service: MoodService = Depends(get_mood_service),
):
    return await service.delete(request)
