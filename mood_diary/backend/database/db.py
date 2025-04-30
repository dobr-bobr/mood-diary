import sqlite3

from mood_diary.backend.repositories.sqlite.user import SQLiteUserRepository as UserRepository
from mood_diary.backend.repositories.sqlite.mood import SQLiteMoodRepository as MoodRepository

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)

    UserRepository(conn).init_db()
    MoodRepository(conn).init_db()

    conn.close()
