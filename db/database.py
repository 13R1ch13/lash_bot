import sqlite3
from datetime import datetime, timedelta
from services.services import services

DB_PATH = "appointments.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                service TEXT,
                date TEXT,
                time TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT
            )
            """
        )
        conn.commit()

def save_user(user_id, username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO users (id, username)
            VALUES (?, ?)
            """,
            (user_id, username),
        )
        conn.commit()

def get_all_users():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users")
        return cursor.fetchall()

def save_appointment(user_id, username, service, date, time):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (user_id, username, service, date, time)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, service, date, time))
        conn.commit()

def get_user_appointments(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT service, date, time FROM appointments
            WHERE user_id = ?
            ORDER BY date, time
        """, (user_id,))
        return cursor.fetchall()

def get_appointments_for_date(date):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT time, service FROM appointments
            WHERE date = ?
        """, (date,))
        return cursor.fetchall()

def is_time_range_available(date, start_time_str, duration_minutes):
    """
    Проверяет, что выбранное время + длительность услуги
    не пересекаются с уже записанными процедурами в этот день
    """
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = start_time + timedelta(minutes=duration_minutes)

    appointments = get_appointments_for_date(date)

    for booked_time_str, service in appointments:
        booked_start = datetime.strptime(booked_time_str, "%H:%M")
        booked_end = booked_start + timedelta(minutes=services.get(service, 0))

        if not (end_time <= booked_start or start_time >= booked_end):
            return False

    return True
def delete_user_appointment(user_id, service, date, time):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM appointments
            WHERE user_id = ? AND service = ? AND date = ? AND time = ?
        """, (user_id, service, date, time))
        conn.commit()


def get_service_counts(start_date=None, end_date=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = "SELECT service, COUNT(*) FROM appointments"
        params = []
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        query += " GROUP BY service"
        cursor.execute(query, params)
        return cursor.fetchall()
