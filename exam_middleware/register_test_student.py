import asyncio
import sys
import os
sys.path.append(os.getcwd())
from app.db.database import get_db
from app.db.models import StudentUsernameRegister
from sqlalchemy import select, delete

async def register():
    print("Connecting to database...")
    async for db in get_db():
        # Clean up existing if any (to be sure)
        print("Deleting existing mapping if any...")
        await db.execute(delete(StudentUsernameRegister).where(StudentUsernameRegister.moodle_username == '22007928'))
        
        print("Inserting new mapping...")
        mapping = StudentUsernameRegister(
            moodle_username='22007928',
            register_number='212222240047'
        )
        db.add(mapping)
        await db.commit()
        print("Registered student 22007928 to 212222240047")
        break

if __name__ == "__main__":
    asyncio.run(register())
