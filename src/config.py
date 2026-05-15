"""
src/config.py

Централізовані налаштування проєкту Olist.

Читає змінні з .env і надає:
- PROJECT_ROOT, DATA_DIR — шляхи до файлів
- DATABASE_URL                     — рядок підключення до PostgreSQL
- get_engine()                     — SQLAlchemy engine для роботи з БД
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

load_dotenv()

# ── Шляхи ────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("CSV_DATA_DIR", str(PROJECT_ROOT / "data" / "raw")))

# ── База даних ───────────────────────────────────────────────

DATABASE_URL: str | None = os.getenv("DATABASE_URL")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Повертає SQLAlchemy engine для підключення до PostgreSQL.

    Engine створюється один раз (singleton через lru_cache)
    і перевикористовується при кожному наступному виклику.

    Raises:
        ValueError: якщо DATABASE_URL відсутній у .env.
    """
    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL не знайдено. "
            "Створи файл .env з рядком: "
            "DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/olist_db"
        )
    return create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
