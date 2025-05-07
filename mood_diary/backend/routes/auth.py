from uuid import UUID
import json
import logging

from fastapi import APIRouter, Response, Depends, status
import redis.asyncio as aioredis

from mood_diary.backend.routes.dependencies import (
    get_current_user_id,
    get_user_service,
)
from mood_diary.backend.services.user import UserService
from mood_diary.common.api.schemas.auth import (
    RegisterRequest,
    Profile,
    LoginRequest,
    ChangePasswordRequest,
    ChangeProfileRequest,
)
from mood_diary.common.api.schemas.common import MessageResponse

from mood_diary.backend.config import config
from mood_diary.backend.database.cache import get_redis_client

logger = logging.getLogger("mood_diary.backend.app")

router = APIRouter()


@router.post(
    "/register",
    response_model=Profile,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Profile,
            "description": "User registered successfully",
        },
        400: {
            "model": MessageResponse,
            "description": "Username already exists",
            "content": {
                "application/json": {
                    "example": {"message": "Username already exists"}
                }
            },
        },
    },
)
async def register(
    request: RegisterRequest, service: UserService = Depends(get_user_service)
):
    logger.info(f"Attempting registration for username: {request.username}")
    try:
        profile = await service.register(request)
        logger.info(
            f"User registered successfully. "
            f"User ID: {profile.id}, Username: {profile.username}"
        )
        return profile
    except Exception as e:
        logger.error(
            f"Registration failed for username {request.username}: {e}"
        )
        raise


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "User logged in successfully",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponse,
            "description": "Incorrect password or username does not exist",
            "content": {
                "application/json": {
                    "example": {
                        "message": (
                            "Incorrect password or username does not exist"
                        )
                    }
                }
            },
        },
    },
)
async def login(
    request: LoginRequest, service: UserService = Depends(get_user_service)
):
    logger.info(f"Login attempt for username: {request.username}")
    try:
        login_response = await service.login(request)
        logger.info(f"Login successful for username: {request.username}")
        response = Response(status_code=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=login_response.access_token,
            httponly=True,
            samesite="lax",
            secure=config.AUTH_SECURE_COOKIE,
        )
        return response
    except Exception as e:
        logger.error(f"Login failed for username {request.username}: {e}")
        raise


@router.post(
    "/validate",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Token is valid"},
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponse,
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid or expired token"}
                }
            },
        },
    },
)
async def validate_token(user_id: UUID = Depends(get_current_user_id)):
    logger.info(f"Token validation attempt for User ID: {user_id}")
    logger.info(f"Token validation successful for User ID: {user_id}")
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/profile",
    response_model=Profile,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Profile,
            "description": "User profile retrieved successfully",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponse,
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid or expired token"}
                }
            },
        },
    },
)
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    logger.info(f"Fetching profile for User ID: {user_id}")
    cache_key = f"profile:{user_id}"
    cached_profile = await redis.get(cache_key)

    if cached_profile:
        logger.info(f"Profile cache hit for User ID: {user_id}")
        return Profile(**json.loads(cached_profile))

    logger.info(f"Profile cache miss for User ID: {user_id}")
    profile = await service.get_profile(user_id)
    await redis.set(
        cache_key, profile.model_dump_json(), ex=config.REDIS_CACHE_TTL
    )
    logger.info(f"Profile fetched and cached for User ID: {user_id}")
    return profile


@router.put(
    "/password",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Password changed successfully"},
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponse,
            "description": "Incorrect old password",
            "content": {
                "application/json": {
                    "example": {"message": "Incorrect old password"}
                }
            },
        },
    },
)
async def change_password(
    request: ChangePasswordRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    logger.info(f"Password change attempt for User ID: {user_id}")
    try:
        await service.change_password(user_id, request)
        cache_key = f"profile:{user_id}"
        await redis.delete(cache_key)
        logger.info(
            f"Password changed successfully for User ID: {user_id}. "
            f"Profile cache invalidated."
        )
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Password change failed for User ID {user_id}: {e}")
        raise


@router.put(
    "/profile",
    response_model=Profile,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Profile,
            "description": "User profile updated successfully",
        }
    },
)
async def update_profile(
    request: ChangeProfileRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    logger.info(
        f"Profile update attempt for User ID: {user_id}. "
        f"New name: {request.name}"
    )
    try:
        profile = await service.update_profile(user_id, request)
        cache_key = f"profile:{user_id}"
        await redis.delete(cache_key)
        logger.info(
            f"Profile updated successfully for User ID: {user_id}. "
            f"Profile cache invalidated."
        )
        return profile
    except Exception as e:
        logger.error(f"Profile update failed for User ID {user_id}: {e}")
        raise
