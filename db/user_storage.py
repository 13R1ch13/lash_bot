import sqlite3
from typing import List

USER_DB_PATH = "users.db"


def init_user_db() -> None:
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
            """
        )
        conn.commit()


def add_user(user_id: int) -> None:
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()


def get_all_users() -> List[int]:
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]

init_user_db()
