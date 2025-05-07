from uuid import UUID
import json

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
    return await service.register(request)


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
    login_response = await service.login(request)
    response = Response(status_code=status.HTTP_200_OK)
    response.set_cookie(
        key="access_token",
        value=login_response.access_token,
        httponly=True,
        samesite="lax",
        secure=config.AUTH_SECURE_COOKIE,
    )
    return response


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
    cache_key = f"profile:{user_id}"
    cached_profile = await redis.get(cache_key)

    if cached_profile:
        return Profile(**json.loads(cached_profile))

    profile = await service.get_profile(user_id)
    await redis.set(
        cache_key, profile.model_dump_json(), ex=config.REDIS_CACHE_TTL
    )
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
    result = await service.change_password(user_id, request)
    cache_key = f"profile:{user_id}"
    await redis.delete(cache_key)
    return result


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
    profile = await service.update_profile(user_id, request)
    cache_key = f"profile:{user_id}"
    await redis.delete(cache_key)
    return profile
