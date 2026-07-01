import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "certificates.db")


def get_database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return ""

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"

    return url


def is_postgres():
    return bool(get_database_url())


def _check_render_config():
    if os.environ.get("RENDER") and not is_postgres():
        raise RuntimeError(
            "DATABASE_URL is missing on Render. "
            "Add your Neon PostgreSQL connection string in Render → Environment."
        )


def get_db():
    _check_render_config()

    if is_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor

        return psycopg2.connect(get_database_url(), cursor_factory=RealDictCursor)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_session():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(conn, sql, params=()):
    if is_postgres():
        sql = sql.replace("?", "%s")
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def fetchone(cur):
    row = cur.fetchone()
    return dict(row) if row is not None else None


def fetchall(cur):
    return [dict(r) for r in cur.fetchall()]


def init_db():
    with db_session() as conn:
        cur = conn.cursor()

        if is_postgres():
            statements = [
                """
                CREATE TABLE IF NOT EXISTS batches (
                    id SERIAL PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    template TEXT NOT NULL DEFAULT 'classic',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS certificates (
                    id SERIAL PRIMARY KEY,
                    unique_id TEXT UNIQUE NOT NULL,
                    batch_id INTEGER NOT NULL REFERENCES batches(id),
                    student_name TEXT NOT NULL,
                    course TEXT,
                    date TEXT
                )
                """,
            ]
            for stmt in statements:
                cur.execute(stmt)
        else:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    template TEXT NOT NULL DEFAULT 'classic',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_id TEXT UNIQUE NOT NULL,
                    batch_id INTEGER NOT NULL,
                    student_name TEXT NOT NULL,
                    course TEXT,
                    date TEXT,
                    FOREIGN KEY (batch_id) REFERENCES batches(id)
                );
            """)
