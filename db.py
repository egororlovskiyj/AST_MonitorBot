import asyncpg
from config import DATABASE_URL

async def get_conn():
    return await asyncpg.connect(DATABASE_URL)

async def init_db():
    conn = await get_conn()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS account_cache (
            username TEXT PRIMARY KEY,
            last_reels_date DATE,
            last_post_date DATE,
            has_story BOOLEAN
        );
    """)
    await conn.close()

async def update_cache(username, reels, post, story):
    conn = await get_conn()
    await conn.execute("""
        INSERT INTO account_cache(username, last_reels_date, last_post_date, has_story)
        VALUES($1,$2,$3,$4)
        ON CONFLICT(username)
        DO UPDATE SET
            last_reels_date = EXCLUDED.last_reels_date,
            last_post_date = EXCLUDED.last_post_date,
            has_story = EXCLUDED.has_story;
    """, username, reels, post, story)
    await conn.close()

async def get_cache(username):
    conn = await get_conn()
    row = await conn.fetchrow("SELECT * FROM account_cache WHERE username=$1", username)
    await conn.close()
    return row
