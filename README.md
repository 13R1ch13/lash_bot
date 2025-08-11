# Lash Bot

This project is a Telegram bot for managing appointments.

## Database initialization

The bot stores its data in a SQLite database located in `appointments.db`.
To create the database and the required tables, run the `init_db()` function:

```bash
python -c "from db.database import init_db; init_db()"
```

Running `main.py` also calls `init_db()` automatically before starting the bot.
