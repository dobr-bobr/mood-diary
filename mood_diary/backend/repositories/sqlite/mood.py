from datetime import datetime, date
from uuid import UUID, uuid4

from mood_diary.backend.exceptions.mood import MoodStampAlreadyExists
from mood_diary.backend.repositories.mood import MoodStampRepository
from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodStamp,
    MoodStampFilter,
)


class SQLiteMoodRepository(MoodStampRepository):
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

    async def get(self, user_id: UUID, date: date) -> MoodStamp | None:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM moodStamps WHERE date = ? AND user_id = ?",
            date,
            user_id,
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

    async def get_many(
            self, user_id: UUID, body: MoodStampFilter
    ) -> list[MoodStamp] | None:
        cursor = self.connection.cursor()
        query = "SELECT * FROM moodStamps WHERE 1=1"
        params: list[str | date | int] = []

        if body.user_id is not None:
            query += " AND user_id = ?"
            params.append(str(user_id))
        if body.start_date is not None:
            query += " AND date >= ?"
            params.append(body.start_date)
        if body.end_date is not None:
            query += " AND date <= ?"
            params.append(body.end_date)
        if body.value is not None:
            query += " AND value = ?"
            params.append(body.value)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            MoodStamp(
                id=UUID(row[0]),
                user_id=row[1],
                date=row[2],
                value=row[3],
                note=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]

    async def create(
            self, user_id: UUID, body: CreateMoodStamp
    ) -> MoodStamp | None:
        """
        Create new moodstamp.
        Returns None if moodstamp with the same entry date already exists
        """

        cursor = self.connection.cursor()

        cursor.execute(
            "SELECT id FROM moodStamps WHERE user_id = ? AND date = ?",
            (str(user_id), body.date),
        )
        if cursor.fetchone():
            raise MoodStampAlreadyExists()

        stamp_id = uuid4()
        created_at = updated_at = datetime.now()

        cursor.execute(
            """INSERT INTO moodStamps
            (id, user_id, date, value, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(stamp_id),
                str(user_id),
                body.date,
                body.value,
                body.note,
                created_at,
                updated_at,
            ),
        )
        self.connection.commit()

        return MoodStamp(
            id=stamp_id,
            user_id=body.user_id,
            date=body.date,
            value=body.value,
            note=body.note,
            created_at=created_at,
            updated_at=updated_at,
        )

    async def update(
            self, user_id: UUID, date: date, body: UpdateMoodStamp
    ) -> MoodStamp | None:
        """Update moodstamp by date. Returns None if moodstamp not found"""
        cursor = self.connection.cursor()

        # First get the existing stamp
        cursor.execute(
            "SELECT * FROM moodStamps WHERE user_id = ? AND date = ?",
            (str(user_id), date),
        )
        row = cursor.fetchone()
        if not row:
            return None

        updated_at = datetime.now()
        update_values = {
            "value": body.value if body.value is not None else row[3],
            "note": body.note if body.note is not None else row[4],
            "updated_at": updated_at,
        }

        # Perform the update
        cursor.execute(
            """UPDATE moodStamps
            SET value = ?, note = ?, updated_at = ?
            WHERE user_id = ? AND date = ?""",
            (
                update_values["value"],
                update_values["note"],
                update_values["updated_at"],
                str(user_id),
                date,
            ),
        )
        self.connection.commit()

        return MoodStamp(
            id=UUID(row[0]),
            user_id=user_id,
            date=date,
            value=update_values["value"],
            note=update_values["note"],
            created_at=row[5],
            updated_at=updated_at,
        )

    async def delete(
            self, user_id: UUID, date: date
    ) -> MoodStamp | None:
        """Delete moodstamp by date. Returns None if stamp not found"""
        cursor = self.connection.cursor()

        # First get the stamp to return it
        cursor.execute(
            "SELECT * FROM moodStamps WHERE user_id = ? AND date = ?",
            (str(user_id), date),
        )
        row = cursor.fetchone()
        if not row:
            return None

        # Delete the stamp
        cursor.execute(
            "DELETE FROM moodStamps WHERE user_id = ? AND date = ?",
            (str(user_id), date),
        )
        self.connection.commit()

        return MoodStamp(
            id=UUID(row[0]),
            user_id=user_id,
            date=date,
            value=row[3],
            note=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
