import asyncio
import logging
from app.db.database import engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_db():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE subject_mappings ADD COLUMN target_site_url VARCHAR;"))
            logger.info("Successfully added target_site_url to subject_mappings")
    except Exception as e:
        logger.error(f"Error during migration: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_db())
