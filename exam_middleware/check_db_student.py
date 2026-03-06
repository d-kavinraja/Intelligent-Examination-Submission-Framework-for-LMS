import asyncio
import sys
import os

# Set up path to import app modules
sys.path.append(os.getcwd())

from app.db.database import get_db
from app.db.models import StudentUsernameRegister
from sqlalchemy import select

async def check():
    print("Checking database for student mapping...")
    async for db in get_db():
        result = await db.execute(select(StudentUsernameRegister).where(StudentUsernameRegister.moodle_username == '22007928'))
        mapping = result.scalar_one_or_none()
        if mapping:
            print(f"FOUND: Moodle Username: {mapping.moodle_username}, Register Number: {mapping.register_number}")
        else:
            print("NOT FOUND: No mapping for moodle_username '22007928'")
        break

if __name__ == "__main__":
    asyncio.run(check())
