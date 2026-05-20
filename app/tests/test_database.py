from unittest.mock import MagicMock, patch

import pytest
from src.config import Settings
from src.database import Database


def _settings() -> Settings:
    return Settings(
        app_name="test",
        app_version="0",
        app_env="test",
        db_host="localhost",
        db_port=5432,
        db_name="db",
        db_user="user",
        db_password="pass",
        db_pool_min=1,
        db_pool_max=2,
        db_connect_retries=2,
        db_connect_retry_delay_sec=0.0,
        default_limit=20,
        max_limit=100,
    )


@patch("psycopg2.pool.SimpleConnectionPool")
def test_database_connect_and_disconnect(mock_pool_cls: MagicMock) -> None:
    mock_pool = MagicMock()
    mock_pool_cls.return_value = mock_pool
    db = Database(_settings())

    db.connect()
    db.connect()

    mock_pool_cls.assert_called_once()
    db.disconnect()
    mock_pool.closeall.assert_called_once()
    assert db._pool is None


@patch("psycopg2.pool.SimpleConnectionPool")
def test_database_connect_retries_then_fails(mock_pool_cls: MagicMock) -> None:
    import psycopg2

    mock_pool_cls.side_effect = psycopg2.OperationalError("down")
    db = Database(_settings())

    with pytest.raises(RuntimeError, match="Failed to initialize database pool"):
        db.connect()


def test_database_cursor_requires_pool() -> None:
    db = Database(_settings())
    with pytest.raises(RuntimeError, match="not connected"):
        with db.cursor():
            pass


@patch("psycopg2.pool.SimpleConnectionPool")
def test_database_cursor_and_ping(mock_pool_cls: MagicMock) -> None:
    mock_pool = MagicMock()
    mock_pool_cls.return_value = mock_pool
    mock_conn = MagicMock()
    mock_pool.getconn.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None

    mock_cur = MagicMock()
    mock_cur.__enter__.return_value = mock_cur
    mock_cur.__exit__.return_value = None
    mock_cur.fetchone.return_value = {"ok": 1}
    mock_conn.cursor.return_value = mock_cur

    db = Database(_settings())
    db.connect()

    with db.cursor() as cur:
        cur.execute("SELECT 1;")
        assert cur.fetchone() == {"ok": 1}

    assert db.ping() is True
    mock_pool.putconn.assert_called()


def test_database_ping_failure() -> None:
    db = Database(_settings())
    db._pool = MagicMock()
    db._pool.getconn.side_effect = OSError("broken")

    assert db.ping() is False
