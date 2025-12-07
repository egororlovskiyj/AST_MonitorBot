# db.py
import datetime as dt
import asyncpg

from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, max_size=5)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                ts TIMESTAMPTZ NOT NULL,
                story BOOLEAN,
                reels BOOLEAN,
                photo BOOLEAN,
                followers INTEGER,
                banned BOOLEAN,
                error TEXT
            );
            """
        )

        # индексы
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_activity_username_ts ON activity(username, ts DESC);"
        )


async def save_result(
    username: str,
    has_story: bool,
    has_reels: bool,
    has_photo: bool,
    followers: int | None,
    banned: bool,
    error: str | None,
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO activity (username, ts, story, reels, photo, followers, banned, error)
            VALUES ($1, NOW(), $2, $3, $4, $5, $6, $7);
            """,
            username,
            has_story,
            has_reels,
            has_photo,
            followers,
            banned,
            error,
        )


async def get_prev_followers(username: str) -> int | None:
    """Последнее значение followers до сегодняшнего дня."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT followers
            FROM activity
            WHERE username = $1
              AND followers IS NOT NULL
            ORDER BY ts DESC
            LIMIT 1;
            """,
            username,
        )
    if row:
        return row["followers"]
    return None


async def get_inactive_users(days: int = 3) -> list[str]:
    """
    Юзеры, у которых N дней подряд НЕ было ни сторис, ни рилсов, ни фоток.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        since = dt.datetime.utcnow() - dt.timedelta(days=days)
        rows = await conn.fetch(
            """
            SELECT username, ts, story, reels, photo
            FROM activity
            WHERE ts >= $1;
            """,
            since,
        )

    per_user: dict[str, list[tuple[dt.datetime, bool]]] = {}
    for r in rows:
        u = r["username"]
        has_any = bool(r["story"] or r["reels"] or r["photo"])
        per_user.setdefault(u, []).append((r["ts"], has_any))

    inactive = []
    for u, entries in per_user.items():
        # берём последние N записей (по времени)
        entries.sort(key=lambda x: x[0], reverse=True)
        last = entries[:days]
        if len(last) < days:
            continue
        if all(not has for _, has in last):
            inactive.append(u)

    return inactive


async def get_last_status(username: str):
    """Последняя запись по юзеру — пригодится, если захочешь потом расширять."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM activity
            WHERE username = $1
            ORDER BY ts DESC
            LIMIT 1;
            """,
            username,
        )
    return row
