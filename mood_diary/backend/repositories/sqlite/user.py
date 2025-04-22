import sqlite3
from datetime import UTC, datetime
from uuid import UUID, uuid4

from mood_diary.backend.repositories.sсhemas.user import (
    UpdateUserHashedPassword,
    User,
    UpdateUserProfile,
    CreateUser,
)
from mood_diary.backend.repositories.user import UserRepository


class SQLiteUserRepository(UserRepository):
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

    async def get(self, user_id: UUID) -> User | None:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (str(user_id),),
        )
        row = cursor.fetchone()
        if row:
            return User(
                id=UUID(row[0]),
                username=row[1],
                name=row[2],
                hashed_password=row[3],
                created_at=row[4],
                updated_at=row[5],
                password_updated_at=row[6],
            )
        return None

    async def get_by_username(self, username: str) -> User | None:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row:
            return User(
                id=UUID(row[0]),
                username=row[1],
                name=row[2],
                hashed_password=row[3],
                created_at=row[4],
                updated_at=row[5],
                password_updated_at=row[6],
            )
        return None

    async def create(self, body: CreateUser) -> User | None:
        cursor = self.connection.cursor()
        try:
            now = datetime.now(UTC)

            cursor.execute(
                """
                INSERT INTO users (
                    id,
                    username,
                    name,
                    hashed_password,
                    created_at,
                    updated_at,
                    password_updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    body.username,
                    body.name,
                    body.hashed_password,
                    now,
                    now,
                    now,
                ),
            )
            self.connection.commit()
            return await self.get_by_username(body.username)
        except sqlite3.IntegrityError:
            # User with the same username already exists
            return None

    async def update_profile(
        self, user_id: UUID, body: UpdateUserProfile
    ) -> User | None:
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE users SET name = ?, updated_at = ? WHERE id = ?",
            (body.name, datetime.now(UTC), str(user_id)),
        )
        self.connection.commit()
        return await self.get(user_id)

    async def update_hashed_password(
        self, user_id: UUID, body: UpdateUserHashedPassword
    ) -> User | None:
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE users"
            "SET hashed_password = ?, password_updated_at = ?"
            "WHERE id = ?",
            (body.hashed_password, datetime.now(UTC), str(user_id)),
        )
        self.connection.commit()
        return await self.get(user_id)
