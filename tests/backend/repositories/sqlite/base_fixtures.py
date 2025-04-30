import sqlite3
from unittest.mock import MagicMock, AsyncMock

import pytest


@pytest.fixture
def mock_cursor():
    cursor = MagicMock(spec=sqlite3.Cursor)
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    conn = AsyncMock(spec=sqlite3.Connection)
    conn.cursor.return_value = mock_cursor
    conn.commit = MagicMock()
    conn.close = MagicMock()
    return conn
