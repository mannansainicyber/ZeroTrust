import os
import sqlite3

DB_PATH: str = os.environ.get("DATABASE_URL", "zerotrust.db")

VALID_PRIORITIES: frozenset[str] = frozenset({"High", "Medium", "Low"})


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS issues (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                ref      TEXT NOT NULL,
                title    TEXT NOT NULL,
                project  TEXT NOT NULL,
                priority TEXT NOT NULL,
                date     TEXT NOT NULL,
                owner_id INTEGER,
                status   TEXT DEFAULT 'active',
                FOREIGN KEY(owner_id) REFERENCES users(id)
            );
        """)
        conn.commit()


def build_next_ref(conn: sqlite3.Connection) -> str:
    count = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
    return f"FIG-{100 + count + 1}"


def build_issue_query(
    status: str,
    priority: str,
    project: str,
    owner_id: int,
) -> tuple[str, list]:
    sql: str = "SELECT * FROM issues WHERE status=? AND owner_id=?"
    params: list = [status, owner_id]

    if priority and priority in VALID_PRIORITIES:
        sql += " AND priority=?"
        params.append(priority)

    if project:
        sql += " AND project=?"
        params.append(project)

    return sql + " ORDER BY id DESC", params