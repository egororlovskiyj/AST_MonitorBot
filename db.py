# db.py

import asyncpg
from config import DATABASE_URL


async def get_conn():
    """
    Открываем соединение с PostgreSQL, используя DATABASE_URL
    из переменной окружения.
    """
    return await asyncpg.connect(DATABASE_URL)


async def init_db():
    """
    Инициализация базы:
    - если таблица account_cache уже есть — удаляем её
      (нужно, чтобы избавиться от старой версии с типами DATE)
    - создаём таблицу заново с нужными типами (BOOLEAN)
    """
    conn = await get_conn()

    # Удаляем старую таблицу, если она была создана с неправильными типами
    await conn.execute("""
        DROP TABLE IF EXISTS account_cache;
    """)

    # Создаём таблицу с правильными типами
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS account_cache (
            username TEXT PRIMARY KEY,
            last_reels_date BOOLEAN,
            last_post_date  BOOLEAN,
            has_story       BOOLEAN
        );
    """)

    await conn.close()


async def update_cache(username, reels, post, story):
    """
    Обновляем/создаём запись в кэше.
    Ожидается, что reels, post, story — булевые значения (True/False).
    """
    conn = await get_conn()
    await conn.execute(
        """
        INSERT INTO account_cache(username, last_reels_date, last_post_date, has_story)
        VALUES($1, $2, $3, $4)
        ON CONFLICT(username)
        DO UPDATE SET
            last_reels_date = EXCLUDED.last_reels_date,
            last_post_date  = EXCLUDED.last_post_date,
            has_story       = EXCLUDED.has_story;
        """,
        username, reels, post, story
    )
    await conn.close()


async def get_cache(username):
    """
    Возвращает одну строку из account_cache по username
    или None, если записи нет.
    """
    conn = await get_conn()
    row = await conn.fetchrow(
        "SELECT * FROM account_cache WHERE username = $1",
        username
    )
    await conn.close()
    return row

