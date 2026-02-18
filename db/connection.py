"""
PostgreSQL connection pool and initialization.
Handles connection errors with retries. Never logs credentials.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import connection as PgConnection

# Module-level connection pool (lazy init)
_connection_pool: pool.ThreadedConnectionPool | None = None


def get_database_url() -> str:
    """Read DATABASE_URL from environment. Required for deployment."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return url


def get_connection(
    max_retries: int = 3,
    retry_delay_sec: float = 2.0,
) -> PgConnection:
    """
    Get a connection from the pool. Retries on connection failure.
    Caller must close the connection or use as context manager.
    """
    global _connection_pool
    url = get_database_url()

    if _connection_pool is None:
        last_error = None
        for attempt in range(max_retries):
            try:
                _connection_pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=url,
                )
                break
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay_sec)
        else:
            raise last_error  # type: ignore

    return _connection_pool.getconn()


@contextmanager
def get_cursor():
    """Context manager: get connection, yield cursor, then close connection."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        finally:
            cur.close()
    finally:
        _connection_pool.returnconn(conn)  # type: ignore


def init_db() -> None:
    """
    Create all tables if they do not exist.
    Run this on app startup (dashboard and worker).
    """
    from db.migrations import run_migrations

    run_migrations()
