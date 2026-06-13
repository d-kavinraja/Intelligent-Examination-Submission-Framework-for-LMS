import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def fetch_artifacts():
    url = os.environ.get("DATABASE_URL").replace("postgresql+asyncpg", "postgres")
    try:
        conn = await asyncpg.connect(url)
        print("--- EXAMINATION ARTIFACTS ---")
        rows = await conn.fetch('SELECT id, artifact_uuid, parsed_reg_no, parsed_subject_code, exam_type, attempt_number, attempt_2_locked, workflow_status FROM examination_artifacts')
        for r in rows:
            print(f"ID: {r['id']}, UUID: {r['artifact_uuid']}, Reg: {r['parsed_reg_no']}, Subject: {r['parsed_subject_code']}, Exam: {r['exam_type']}, Attempt: {r['attempt_number']}, Locked: {r['attempt_2_locked']}, Status: {r['workflow_status']}")
        
        print("\n--- EXAM SUBMISSIONS ---")
        sub_rows = await conn.fetch('SELECT id, student_id, subject_code, exam_type, attempt_number, status, target_site_url FROM exam_submissions')
        for r in sub_rows:
            print(f"ID: {r['id']}, Student: {r['student_id']}, Subject: {r['subject_code']}, Exam: {r['exam_type']}, Attempt: {r['attempt_number']}, Status: {r['status']}, URL: {r['target_site_url']}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_artifacts())
