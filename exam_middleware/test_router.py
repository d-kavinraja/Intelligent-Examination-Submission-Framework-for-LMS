import asyncio
import sys
import traceback

def run():
    try:
        from app.db.database import async_session_maker
        from app.api.routes.auth import register_student_mapping
        from app.schemas.schemas import StudentLoginRequest
        import app.db.models
        from sqlalchemy.future import select
    except Exception as e:
        print("Import error: ")
        traceback.print_exc()
        return

    async def _test():
        creds = StudentLoginRequest(
            username="testuser",
            password="Password@123",
            register_number="212222240047"
        )
        try:
            async with async_session_maker() as db:
                res = await register_student_mapping(credentials=creds, db=db)
                print(res)
        except Exception as e:
            print("Execution error: ")
            traceback.print_exc()
            
    asyncio.run(_test())

if __name__ == "__main__":
    run()
