from fastapi import status

from mood_diary.backend.exceptions.base import BaseApplicationException


class MoodStampAlreadyExist(BaseApplicationException):
    def __init__(self):
        super().__init__("MoodStamp already exists", status.HTTP_400_BAD_REQUEST)


class MoodStampNotExist(BaseApplicationException):
    def __init__(self):
        super().__init__("MoodStamp does not exist", status.HTTP_404_NOT_FOUND)


class IncorrectMoodNote(BaseApplicationException):
    def __init__(self):
        super().__init__("MoodNote in wrong format", status.HTTP_422_UNPROCESSABLE_ENTITY)


class IncorrectMoodValue(BaseApplicationException):
    def __init__(self):
        super().__init__("MoodValue in wrong format", status.HTTP_422_UNPROCESSABLE_ENTITY)
