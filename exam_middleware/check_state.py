import asyncio
import asyncpg
import sys
import os

# Add the current directory to sys.path to import app
sys.path.append(os.getcwd())

from app.core.config import settings

async def check():
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        rows = await conn.fetch("SELECT * FROM student_username_register WHERE moodle_username = '22007928'")
        print(f"Student mapping for 22007928: {rows}")
        
        # Also check subject mappings
        subjects = await conn.fetch("SELECT subject_code, target_site_url FROM subject_mappings")
        print(f"Current subject mappings: {subjects}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
