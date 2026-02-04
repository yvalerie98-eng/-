import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("bot.db")

@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    try:
        yield c
        c.commit()
    finally:
        c.close()

def init_db():
    with conn() as c:
        c.execute(
        """
        CREATE TABLE IF NOT EXISTS counters (
          amount_key TEXT PRIMARY KEY,
          next_no INTEGER NOT NULL
        )
        """
        )
        c.execute(
        """
        CREATE TABLE IF NOT EXISTS states (
          chat_id INTEGER PRIMARY KEY,
          step TEXT,
          payload TEXT
        )
        """
        )

def take_next_no(amount_key: str) -> int:
    with conn() as c:
        row = c.execute(
            "SELECT next_no FROM counters WHERE amount_key=?",
            (amount_key,)
        ).fetchone()

        if row is None:
            c.execute(
                "INSERT INTO counters(amount_key, next_no) VALUES(?, ?)",
                (amount_key, 2)
            )
            return 1

        current = int(row[0])
        c.execute(
            "UPDATE counters SET next_no=? WHERE amount_key=?",
            (current + 1, amount_key)
        )
        return current

def set_state(chat_id: int, step: str, payload: str = ""):
    with conn() as c:
        c.execute(
        """
        INSERT INTO states(chat_id, step, payload)
        VALUES(?, ?, ?)
        ON CONFLICT(chat_id)
        DO UPDATE SET step=excluded.step, payload=excluded.payload
        """
        , (chat_id, step, payload))

def get_state(chat_id: int):
    with conn() as c:
        row = c.execute(
            "SELECT step, payload FROM states WHERE chat_id=?",
            (chat_id,)
        ).fetchone()

        if not row:
            return None

        return {"step": row[0], "payload": row[1]}

def clear_state(chat_id: int):
    with conn() as c:
        c.execute("DELETE FROM states WHERE chat_id=?", (chat_id,))
