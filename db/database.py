import aiosqlite
from datetime import datetime, timedelta
from services.services import services

DB_PATH = "appointments.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
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
        await conn.commit()

async def save_appointment(user_id, username, service, date, time):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            INSERT INTO appointments (user_id, username, service, date, time)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username, service, date, time),
        )
        await conn.commit()

async def get_user_appointments(user_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            """
            SELECT service, date, time FROM appointments
            WHERE user_id = ?
            ORDER BY date, time
            """,
            (user_id,),
        )
        return await cursor.fetchall()

async def get_appointments_for_date(date):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            """
            SELECT time, service FROM appointments
            WHERE date = ?
            """,
            (date,),
        )
        return await cursor.fetchall()

async def is_time_range_available(date, start_time_str, duration_minutes):
    """
    Проверяет, что выбранное время + длительность услуги
    не пересекаются с уже записанными процедурами в этот день
    """
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = start_time + timedelta(minutes=duration_minutes)

    appointments = await get_appointments_for_date(date)

    for booked_time_str, service in appointments:
        booked_start = datetime.strptime(booked_time_str, "%H:%M")
        booked_end = booked_start + timedelta(minutes=services.get(service, 0))

        if not (end_time <= booked_start or start_time >= booked_end):
            return False

    return True

async def delete_user_appointment(user_id, service, date, time):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            DELETE FROM appointments
            WHERE user_id = ? AND service = ? AND date = ? AND time = ?
            """,
            (user_id, service, date, time),
        )
        await conn.commit()


async def get_service_counts(start_date=None, end_date=None):
    async with aiosqlite.connect(DB_PATH) as conn:
        query = "SELECT service, COUNT(*) FROM appointments"
        params = []
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        query += " GROUP BY service"
        cursor = await conn.execute(query, params)
        return await cursor.fetchall()
