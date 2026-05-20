import time
from contextlib import contextmanager

from src.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pool = None

    def connect(self) -> None:
        if self._pool is not None:
            return

        import psycopg2
        from psycopg2.pool import SimpleConnectionPool

        last_error: Exception | None = None
        for _ in range(self.settings.db_connect_retries):
            try:
                self._pool = SimpleConnectionPool(
                    minconn=self.settings.db_pool_min,
                    maxconn=self.settings.db_pool_max,
                    host=self.settings.db_host,
                    port=self.settings.db_port,
                    dbname=self.settings.db_name,
                    user=self.settings.db_user,
                    password=self.settings.db_password,
                )
                return
            except psycopg2.OperationalError as exc:  # pragma: no cover - retry branch
                last_error = exc
                time.sleep(self.settings.db_connect_retry_delay_sec)

        raise RuntimeError("Failed to initialize database pool") from last_error

    def disconnect(self) -> None:
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None

    @contextmanager
    def cursor(self):
        from psycopg2.extras import RealDictCursor

        if self._pool is None:
            raise RuntimeError("Database is not connected")

        connection = self._pool.getconn()
        try:
            with connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cur:
                    yield cur
        finally:
            self._pool.putconn(connection)

    def ping(self) -> bool:
        try:
            with self.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            return True
        except Exception:  # pragma: no cover - runtime health behavior
            return False
