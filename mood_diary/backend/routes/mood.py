import logging
import json
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, status, Path
import redis.asyncio as aioredis

from mood_diary.backend.routes.dependencies import (
    get_mood_service,
    get_current_user_id,
)
from mood_diary.backend.services.mood import MoodService
from mood_diary.common.api.schemas.mood import (
    CreateMoodStampRequest,
    GetManyMoodStampsRequest,
    UpdateMoodStampRequest,
    MoodStampSchema,
)
from mood_diary.common.api.schemas.common import MessageResponse
from mood_diary.backend.config import config
from mood_diary.backend.database.cache import get_redis_client

logger = logging.getLogger("mood_diary.backend.app")

router = APIRouter()


@router.post(
    "/",
    response_model=MoodStampSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": MoodStampSchema,
            "description": "MoodStamp recorded successfully",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": MessageResponse,
            "description": "MoodStamp already exists",
            "content": {
                "application/json": {
                    "example": {"message": "MoodStamp already exists"}
                }
            },
        },
    },
)
async def create(
    request: CreateMoodStampRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: MoodService = Depends(get_mood_service),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    logger.info(
        f"User ID: {user_id} attempting to create mood stamp for date: {request.date}"
    )
    try:
        moodstamp = await service.create(user_id=user_id, body=request)
        logger.info(
            f"User ID: {user_id} created mood stamp ID: {moodstamp.id} for date: {request.date}"
        )
        keys_to_delete = []
        async for key in redis.scan_iter(match=f"moodstamps:{user_id}:*"):
            keys_to_delete.append(key)
        if keys_to_delete:
            await redis.delete(*keys_to_delete)
            logger.info(
                f"User ID: {user_id} invalidated {len(keys_to_delete)} list cache(s) for mood stamps."
            )
        return moodstamp
    except Exception as e:
        logger.error(
            f"User ID: {user_id} failed to create mood stamp for date {request.date}: {e}"
        )
        raise


@router.get(
    "/{date}",
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
                "application/json": {
                    "example": {"message": "MoodStamp does not exist"}
                }
            },
        },
    },
)
async def get_moodstamp(
    date: date = Path(...),
    user_id: UUID = Depends(get_current_user_id),
    service: MoodService = Depends(get_mood_service),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    logger.info(f"User ID: {user_id} fetching mood stamp for date: {date}")
    cache_key = f"moodstamp:{user_id}:{date}"
    cached_moodstamp = await redis.get(cache_key)

    if cached_moodstamp:
        logger.info(
            f"Mood stamp cache hit for User ID: {user_id}, Date: {date}"
        )
        return MoodStampSchema(**json.loads(cached_moodstamp))

    logger.info(f"Mood stamp cache miss for User ID: {user_id}, Date: {date}")
    moodstamp = await service.get(user_id=user_id, date=date)
    if moodstamp:
        await redis.set(
            cache_key, moodstamp.model_dump_json(), ex=config.REDIS_CACHE_TTL
        )
        logger.info(
            f"Mood stamp fetched and cached for User ID: {user_id}, Date: {date}"
        )
    else:
        logger.info(
            f"Mood stamp not found for User ID: {user_id}, Date: {date}"
        )
    return moodstamp


@router.get(
    "/",
    response_model=list[MoodStampSchema],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": list[MoodStampSchema],
            "description": "MoodStamps retrieved successfully",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": MessageResponse,
            "description": "MoodStamps not found",
            "content": {
                "application/json": {
                    "example": {"message": "MoodStamps does not exist"}
                }
            },
        },
    },
)
async def get_many_moodstamps(
    start_date: date | None = None,
    end_date: date | None = None,
    value: int | None = None,
    user_id: UUID = Depends(get_current_user_id),
    service: MoodService = Depends(get_mood_service),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    logger.info(
        f"User ID: {user_id} fetching multiple mood stamps. Filters: start={start_date}, end={end_date}, value={value}"
    )
    cache_key_params = {
        "start_date": start_date.isoformat() if start_date else "None",
        "end_date": end_date.isoformat() if end_date else "None",
        "value": str(value) if value is not None else "None",
    }
    cache_key = f"moodstamps:{user_id}:" + json.dumps(
        cache_key_params, sort_keys=True
    )

    cached_moodstamps = await redis.get(cache_key)

    if cached_moodstamps:
        logger.info(
            f"Mood stamps list cache hit for User ID: {user_id}, Key: {cache_key}"
        )
        return [
            MoodStampSchema(**item) for item in json.loads(cached_moodstamps)
        ]

    logger.info(
        f"Mood stamps list cache miss for User ID: {user_id}, Key: {cache_key}"
    )
    request_schema = GetManyMoodStampsRequest(
        start_date=start_date,
        end_date=end_date,
        value=value,
    )
    moodstamps = await service.get_many(user_id=user_id, body=request_schema)
    if moodstamps:
        await redis.set(
            cache_key,
            json.dumps([ms.model_dump(mode="json") for ms in moodstamps]),
            ex=config.REDIS_CACHE_TTL,
        )
        logger.info(
            f"Mood stamps list fetched and cached for User ID: {user_id}, Key: {cache_key}. Count: {len(moodstamps)}"
        )
    else:
        logger.info(
            f"No mood stamps found for User ID: {user_id} with Key: {cache_key}"
        )
    return moodstamps


@router.put(
    "/{date}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "MoodStamp updated successfully"},
        status.HTTP_404_NOT_FOUND: {
            "model": MessageResponse,
            "description": "MoodStamp not found",
            "content": {
                "application/json": {
                    "example": {"message": "MoodStamp does not exist"}
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": MessageResponse,
            "description": "Value/note are in the wrong format.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Value/note are in the wrong format."
                    }
                }
            },
        },
    },
)
async def update_moodstamp(
    request: UpdateMoodStampRequest,
    date: date = Path(...),
    user_id: UUID = Depends(get_current_user_id),
    service: MoodService = Depends(get_mood_service),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    logger.info(
        f"User ID: {user_id} attempting to update mood stamp for date: {date}"
    )
    try:
        moodstamp = await service.update(
            user_id=user_id, date=date, body=request
        )
        logger.info(f"User ID: {user_id} updated mood stamp for date: {date}")
        keys_to_delete = [f"moodstamp:{user_id}:{date}"]
        async for key in redis.scan_iter(match=f"moodstamps:{user_id}:*"):
            keys_to_delete.append(key)
        if keys_to_delete:
            await redis.delete(*keys_to_delete)
            logger.info(
                f"User ID: {user_id} invalidated {len(keys_to_delete)} cache key(s) for mood stamp date: {date} and lists."
            )
        return moodstamp
    except Exception as e:
        logger.error(
            f"User ID: {user_id} failed to update mood stamp for date {date}: {e}"
        )
        raise


@router.delete(
    "/{date}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    responses={
        status.HTTP_200_OK: {"description": "MoodStamp deleted successfully"},
        status.HTTP_404_NOT_FOUND: {
            "model": MessageResponse,
            "description": "MoodStamp not found",
            "content": {
                "application/json": {
                    "example": {"message": "MoodStamp does not exist"}
                }
            },
        },
    },
)
async def delete_moodstamp(
    date: date = Path(...),
    user_id: UUID = Depends(get_current_user_id),
    service: MoodService = Depends(get_mood_service),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    logger.info(
        f"User ID: {user_id} attempting to delete mood stamp for date: {date}"
    )
    try:
        await service.delete(user_id=user_id, date=date)
        logger.info(f"User ID: {user_id} deleted mood stamp for date: {date}")
        keys_to_delete = [f"moodstamp:{user_id}:{date}"]
        async for key in redis.scan_iter(match=f"moodstamps:{user_id}:*"):
            keys_to_delete.append(key)
        if keys_to_delete:
            await redis.delete(*keys_to_delete)
            logger.info(
                f"User ID: {user_id} invalidated {len(keys_to_delete)} cache key(s) for mood stamp date: {date} and lists."
            )
        return MessageResponse(message="MoodStamp deleted successfully")
    except Exception as e:
        logger.error(
            f"User ID: {user_id} failed to delete mood stamp for date {date}: {e}"
        )
        raise
