import sqlite3
from datetime import UTC, datetime, date
from uuid import UUID, uuid4

from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodStamp
)

from mood_diary.backend.repositories.mood import MoodRepository


class SQLiteMoodRepository(MoodRepository):
    def __init__(self, connection):
        self.connection = connection

    def init_db(self):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS moodstamps (
                id TEXT PRIMARY KEY,
                user_id TEXT FOREIGN KEY,
                date DATE UNIQUE NOT NULL,
                value INT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            )
            """
        )
        self.connection.commit()

    async def get(self, date: date) -> MoodStamp | None:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM moodStamps WHERE date = ?",
            date,
        )
        row = cursor.fetchone()
        if row:
            return MoodStamp(
                id=UUID(row[0]),
                user_id=row[1],
                date=row[2],
                value=row[3],
                note=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
        return None

    async def create(self, body: CreateMoodStamp) -> MoodStamp | None:
        """Create new moodstamp. Returns None if moodstamp with the same entry date already exists"""
        pass

    async def update(
            self, date: UUID, body: UpdateMoodStamp
    ) -> MoodStamp | None:
        """Update moodstamp by date. Returns None if moodstamp not found"""
        pass

    async def delete(self, date: date) -> MoodStamp | None:
        """Delete moodstamp by date. Returns None if stamp not found"""
        pass
