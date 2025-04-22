from fastapi import status

from mood_diary.backend.exceptions.base import BaseApplicationException


class UsernameAlreadyExists(BaseApplicationException):
    def __init__(self):
        super().__init__(
            "Username already exists", status.HTTP_400_BAD_REQUEST
        )


class IncorrectPasswordOrUserDoesNotExists(BaseApplicationException):
    def __init__(self):
        super().__init__(
            "Incorrect password or username does not exist",
            status.HTTP_401_UNAUTHORIZED,
        )


class InvalidOrExpiredRefreshToken(BaseApplicationException):
    def __init__(self):
        super().__init__(
            "Invalid or expired refresh token", status.HTTP_401_UNAUTHORIZED
        )


class UserNotFound(BaseApplicationException):
    def __init__(self):
        super().__init__("User not found", status.HTTP_404_NOT_FOUND)


class IncorrectOldPassword(BaseApplicationException):
    def __init__(self):
        super().__init__(
            "Incorrect old password", status.HTTP_401_UNAUTHORIZED
        )


class InvalidOrExpiredAccessToken(BaseApplicationException):
    def __init__(self):
        super().__init__(
            "Invalid or expired access token", status.HTTP_401_UNAUTHORIZED
        )
