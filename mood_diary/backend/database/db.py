import sqlite3

from mood_diary.backend.repositories.sqlite.user import SQLiteUserRepository


def init_db(db_path: str):
    conn = sqlite3.connect(db_path)

    SQLiteUserRepository(conn).init_db()

    conn.close()
