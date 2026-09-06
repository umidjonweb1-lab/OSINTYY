import sqlite3
from pathlib import Path
from config import settings


def connect():
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


async def init_db():
    conn = connect()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        language TEXT,
        is_bot INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_activity TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        query TEXT NOT NULL,
        search_type TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        target TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS name_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        display_name TEXT NOT NULL,
        username TEXT,
        observed_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS public_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL UNIQUE,
        username TEXT,
        title TEXT,
        chat_type TEXT,
        member_count INTEGER,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_first_name ON users(first_name);
    CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);
    CREATE INDEX IF NOT EXISTS idx_name_history_telegram_id ON name_history(telegram_id);
    CREATE INDEX IF NOT EXISTS idx_searches_user_id ON searches(user_id);
    """)

    # Safe migrations for databases created by an earlier version.
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "last_name" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
    if "is_bot" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_bot INTEGER DEFAULT 0")
    name_cols = {row[1] for row in conn.execute("PRAGMA table_info(name_history)").fetchall()}
    if "username" not in name_cols:
        conn.execute("ALTER TABLE name_history ADD COLUMN username TEXT")
    chat_cols = {row[1] for row in conn.execute("PRAGMA table_info(public_chats)").fetchall()}
    if "member_count" not in chat_cols:
        conn.execute("ALTER TABLE public_chats ADD COLUMN member_count INTEGER")

    conn.commit()
    conn.close()


def upsert_user(user):
    conn = connect()
    conn.execute("""
        INSERT INTO users(telegram_id, username, first_name, last_name, language, is_bot)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
          username=excluded.username,
          first_name=excluded.first_name,
          last_name=excluded.last_name,
          language=excluded.language,
          is_bot=excluded.is_bot,
          last_activity=CURRENT_TIMESTAMP
    """, (
        user.id, user.username, user.first_name, getattr(user, "last_name", None),
        user.language_code, int(bool(getattr(user, "is_bot", False)))
    ))
    conn.commit()
    conn.close()


def add_search(user_id, query, search_type):
    conn = connect()
    conn.execute("INSERT INTO searches(user_id, query, search_type) VALUES (?, ?, ?)",
                 (user_id, query, search_type))
    conn.commit()
    conn.close()


def add_tracking(user_id, target):
    conn = connect()
    conn.execute("INSERT INTO tracking(user_id, target) VALUES (?, ?)", (user_id, target))
    conn.commit()
    conn.close()


def add_name_observation(telegram_id, display_name, username=None):
    conn = connect()
    last = conn.execute(
        "SELECT display_name, username FROM name_history WHERE telegram_id=? ORDER BY id DESC LIMIT 1",
        (telegram_id,)
    ).fetchone()
    if not last or last["display_name"] != display_name or last["username"] != username:
        conn.execute(
            "INSERT INTO name_history(telegram_id, display_name, username) VALUES (?, ?, ?)",
            (telegram_id, display_name, username)
        )
        conn.commit()
    conn.close()


def search_local_users(query, limit=10):
    q = query.strip().lstrip("@").lower()
    if not q:
        return []
    conn = connect()
    rows = conn.execute("""
        SELECT telegram_id, username, first_name, last_name, is_bot, last_activity
        FROM users
        WHERE lower(COALESCE(username,'')) LIKE ?
           OR lower(COALESCE(first_name,'')) LIKE ?
           OR lower(COALESCE(last_name,'')) LIKE ?
           OR CAST(telegram_id AS TEXT) LIKE ?
           OR lower(COALESCE(first_name,'') || ' ' || COALESCE(last_name,'')) LIKE ?
        ORDER BY last_activity DESC
        LIMIT ?
    """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", limit)).fetchall()
    conn.close()
    return rows


def get_local_user(telegram_id):
    conn = connect()
    row = conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    conn.close()
    return row


def get_name_history(telegram_id, limit=10):
    conn = connect()
    rows = conn.execute("""
        SELECT display_name, username, observed_at
        FROM name_history
        WHERE telegram_id=?
        ORDER BY id DESC
        LIMIT ?
    """, (telegram_id, limit)).fetchall()
    conn.close()
    return rows


def user_search_count(telegram_id):
    conn = connect()
    n = conn.execute("SELECT COUNT(*) FROM searches WHERE user_id=?", (telegram_id,)).fetchone()[0]
    conn.close()
    return n


def stats():
    conn = connect()
    data = {
        "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "searches": conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0],
        "tracking": conn.execute("SELECT COUNT(*) FROM tracking WHERE status='active'").fetchone()[0],
    }
    conn.close()
    return data


def all_user_ids():
    conn = connect()
    rows = conn.execute("SELECT telegram_id FROM users").fetchall()
    conn.close()
    return [r[0] for r in rows]
