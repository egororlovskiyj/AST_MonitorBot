import asyncpg
from datetime import datetime, timedelta
import pytz

from config import DATABASE_URL, TIMEZONE

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity (
                username   TEXT NOT NULL,
                day        DATE NOT NULL,
                has_story  BOOLEAN,
                has_reels  BOOLEAN,
                has_photo  BOOLEAN,
                PRIMARY KEY (username, day)
            );
            """
        )


async def save_result(username: str, has_story: bool, has_reels: bool, has_photo: bool):
    """
    Сохраняем результат за сегодня для пользователя (upsert).
    """
    pool = await get_pool()
    tz = pytz.timezone(TIMEZONE)
    day = datetime.now(tz).date()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO activity (username, day, has_story, has_reels, has_photo)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (username, day)
            DO UPDATE SET
                has_story = EXCLUDED.has_story,
                has_reels = EXCLUDED.has_reels,
                has_photo = EXCLUDED.has_photo;
            """,
            username,
            day,
            has_story,
            has_reels,
            has_photo,
        )


async def get_inactive_users(days: int = 3):
    """
    Возвращает список username, у которых N дней подряд нет контента
    (нет сторис, нет рилсов, нет фото).
    Мы смотрим последние N календарных дней.
    """
    pool = await get_pool()
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).date()
    from_day = today - timedelta(days=days - 1)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT username,
                   COUNT(*) AS cnt,
                   SUM(
                       CASE
                           WHEN (COALESCE(has_story,false)
                                 OR COALESCE(has_reels,false)
                                 OR COALESCE(has_photo,false))
                           THEN 1 ELSE 0
                       END
                   ) AS active_days
            FROM activity
            WHERE day >= $1 AND day <= $2
            GROUP BY username
            HAVING COUNT(*) >= $3
               AND SUM(
                       CASE
                           WHEN (COALESCE(has_story,false)
                                 OR COALESCE(has_reels,false)
                                 OR COALESCE(has_photo,false))
                           THEN 1 ELSE 0
                       END
                   ) = 0;
            """,
            from_day,
            today,
            days,
        )

    return [r["username"] for r in rows]


