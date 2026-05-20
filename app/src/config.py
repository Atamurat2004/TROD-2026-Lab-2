import os
from dataclasses import dataclass
from functools import lru_cache


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    app_env: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_pool_min: int
    db_pool_max: int
    db_connect_retries: int
    db_connect_retry_delay_sec: float
    default_limit: int
    max_limit: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Docker Lab 1 API"),
        app_version=os.getenv("APP_VERSION", "1.1.0"),
        app_env=os.getenv("APP_ENV", "dev"),
        db_host=os.getenv("DB_HOST", "db"),
        db_port=_env_int("DB_PORT", 5432),
        db_name=os.getenv("DB_NAME", "tasks_db"),
        db_user=os.getenv("DB_USER", "tasks_user"),
        db_password=os.getenv("DB_PASSWORD", "change_me"),
        db_pool_min=_env_int("DB_POOL_MIN", 1),
        db_pool_max=_env_int("DB_POOL_MAX", 8),
        db_connect_retries=_env_int("DB_CONNECT_RETRIES", 10),
        db_connect_retry_delay_sec=_env_float("DB_CONNECT_RETRY_DELAY_SEC", 1.0),
        default_limit=_env_int("DEFAULT_LIMIT", 20),
        max_limit=_env_int("MAX_LIMIT", 100),
    )
