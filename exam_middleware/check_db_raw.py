import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def fetch_mappings():
    # Fix postgresql+asyncpg for raw connection
    url = os.environ.get("DATABASE_URL").replace("postgresql+asyncpg", "postgres")
    try:
        conn = await asyncpg.connect(url)
        rows = await conn.fetch('SELECT subject_code, target_site_url FROM subject_mappings')
        for row in rows:
            print(f"Subject: {row['subject_code']}, URL: {row['target_site_url']}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_mappings())
