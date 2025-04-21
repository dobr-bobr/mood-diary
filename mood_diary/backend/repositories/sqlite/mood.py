import sqlite3
from datetime import UTC, datetime
from uuid import UUID, uuid4

from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    UpdateMoodNote,
    CreateMoodStamp,
    UpdateMoodType
)

from mood_diary.backend.repositories.mood import MoodRepository


class SQLiteMoodRepository(MoodRepository):
    def __init__(self, connection):
        self.connection = connection

    def init_db(self):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                password_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.commit()

    async def get(self, mood_id: UUID) -> MoodStamp | None:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM moodStamps WHERE id = ?",
            (str(mood_id),),
        )
        row = cursor.fetchone()
        if row:
            return MoodStamp(
                id=UUID(row[0]),
                user_id=row[1],
                entry_time=row[2],
                type=row[3],
                note=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
        return None

    async def create(self, body: CreateMoodStamp) -> MoodStamp | None:
        """Create new user. Returns None if user with the same username already exists"""
        pass

    async def update_profile(
            self, mood_id: UUID, body: UpdateMoodType
    ) -> MoodStamp | None:
        """Update user profile by ID. Returns None if user not found"""
        pass

    async def update_hashed_password(
            self, mood_id: UUID, body: UpdateMoodNote
    ) -> MoodStamp | None:
        """Update user hashed password by ID. Returns None if user not found"""
        pass