import asyncpg
from datetime import datetime
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
        # контент за день
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity (
                username TEXT NOT NULL,
                day DATE NOT NULL,
                has_story BOOLEAN,
                has_reels BOOLEAN,
                has_photo BOOLEAN,
                status TEXT,
                PRIMARY KEY (username, day)
            );
            """
        )

        # динамика подписчиков
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS followers (
                username TEXT NOT NULL,
                day DATE NOT NULL,
                followers INTEGER,
                PRIMARY KEY (username, day)
            );
            """
        )


async def save_activity(username, story, reels, photo, status):
    pool = await get_pool()
    tz = pytz.timezone(TIMEZONE)
    day = datetime.now(tz).date()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO activity(username, day, has_story, has_reels, has_photo, status)
            VALUES ($1,$2,$3,$4,$5,$6)
            ON CONFLICT(username, day)
            DO UPDATE SET
                has_story = EXCLUDED.has_story,
                has_reels = EXCLUDED.has_reels,
                has_photo = EXCLUDED.has_photo,
                status = EXCLUDED.status;
            """,
            username, day, story, reels, photo, status
        )


async def save_followers(username, followers):
    pool = await get_pool()
    tz = pytz.timezone(TIMEZONE)
    day = datetime.now(tz).date()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO followers(username, day, followers)
            VALUES ($1,$2,$3)
            ON CONFLICT(username, day)
            DO UPDATE SET
                followers = EXCLUDED.followers;
            """,
            username, day, followers
        )


async def get_followers_diff(username):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT day, followers
            FROM followers
            WHERE username = $1
            ORDER BY day DESC
            LIMIT 2;
            """,
            username
        )

    if len(rows) < 2:
        return None

    return rows[0]["followers"] - rows[1]["followers"]


async def get_inactive_users(days=3):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT username
            FROM activity
            GROUP BY username
            HAVING SUM(
                CASE WHEN has_story OR has_reels OR has_photo THEN 1 ELSE 0 END
            ) = 0
            AND COUNT(*) >= $1;
            """,
            days
        )
    return [r["username"] for r in rows]

