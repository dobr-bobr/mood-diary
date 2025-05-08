from uuid import UUID

from fastapi import APIRouter, Response, Depends, status
from fastapi_csrf_protect import CsrfProtect

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
from mood_diary.common.api.schemas.token import TokenWithCSRF
from mood_diary.common.api.schemas.common import MessageResponse

from mood_diary.backend.config import config

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
		request: RegisterRequest,
		service: UserService = Depends(get_user_service),
		csrf_protect: CsrfProtect = Depends()
):
	return await service.register(request)


@router.post(
	"/login",
	response_model=TokenWithCSRF,
	status_code=status.HTTP_200_OK,
	responses={
		status.HTTP_200_OK: {
			"model": TokenWithCSRF,
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
		fastapi_response: Response,
		request: LoginRequest,
		service: UserService = Depends(get_user_service),
		csrf_protect: CsrfProtect = Depends()
):
	login_response = await service.login(request)

	fastapi_response.set_cookie(
		key="access_token",
		value=login_response.access_token,
		httponly=True,
		samesite="lax",
		secure=config.AUTH_SECURE_COOKIE,
		path="/",
		max_age=config.AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES,
	)

	csrf_protect.set_csrf_cookie(
		csrf_signed_token=config.CSRF_SECRET_KEY,
		response=fastapi_response
	)
	csrf_header_token, _ = csrf_protect.generate_csrf_tokens()

	response = Response(status_code=status.HTTP_200_OK)
	response.set_cookie(
		key="access_token",
		value=login_response.access_token,
		httponly=True,
		samesite="lax",
		secure=config.AUTH_SECURE_COOKIE,
	)
	return TokenWithCSRF(
		access_token=login_response.access_token,
		csrf_token=csrf_header_token,
	)



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
):
	return await service.get_profile(user_id)


@router.put(
	"/password",
	status_code=status.HTTP_200_OK,
	responses={
		status.HTTP_200_OK: {"description": "Password changed successfully"},
		status.HTTP_400_BAD_REQUEST: {
			"model": MessageResponse,
			"description": "Incorrect old password",
			"content": {
				"application/json": {
					"example": {"message": "Incorrect old password"}
				}
			},
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
async def change_password(
		request: ChangePasswordRequest,
		user_id: UUID = Depends(get_current_user_id),
		service: UserService = Depends(get_user_service),
		csrf_protect: CsrfProtect = Depends()
):
	return await service.change_password(user_id, request)


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
		csrf_protect: CsrfProtect = Depends()
):
	return await service.update_profile(user_id, request)
