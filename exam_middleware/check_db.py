import asyncio
import logging
from app.db.database import async_session_maker
from sqlalchemy import select
from app.db.models import SubjectMapping

# Suppress sqlalchemy logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

async def show_mappings():
    async with async_session_maker() as db:
        res = await db.execute(select(SubjectMapping))
        mappings = res.scalars().all()
        for m in mappings:
            print(f"Subject: {m.subject_code}, URL: {m.target_site_url}, CMID: {m.cmid}")

if __name__ == "__main__":
    asyncio.run(show_mappings())
