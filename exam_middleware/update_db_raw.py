import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def update_mappings():
    url = os.environ.get("DATABASE_URL").replace("postgresql+asyncpg", "postgres")
    try:
        conn = await asyncpg.connect(url)
        await conn.execute("UPDATE subject_mappings SET target_site_url = 'https://lms2.ai.saveetha.in' WHERE subject_code IN ('19AI411', '19AI550')")
        print("Updated mappings successfully")
        
        rows = await conn.fetch('SELECT subject_code, target_site_url FROM subject_mappings')
        for row in rows:
            print(f"Subject: {row['subject_code']}, URL: {row['target_site_url']}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(update_mappings())
