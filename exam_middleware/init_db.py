"""
Database initialization script for Examination Middleware
Creates all tables and seeds initial data
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import engine, Base, async_session_maker
from app.db.models import (
    StaffUser,
    SubjectMapping,
    SystemConfig,
    ExaminationArtifact,
    AuditLog,
)
from app.core.security import get_password_hash


async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables created successfully!")


async def seed_staff_user():
    """Create default admin staff user."""
    async with async_session_maker() as session:
        # Check if admin already exists
        result = await session.execute(
            text("SELECT id FROM staff_users WHERE username = 'admin'")
        )
        existing = result.fetchone()
        
        if not existing:
            admin = StaffUser(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator",
                email="admin@example.com",
                role="admin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print("✓ Created default admin user (username: admin, password: admin123)")
        else:
            print("✓ Admin user already exists")


async def seed_subject_mappings():
    """Seed subject to Moodle assignment mappings."""
    # Based on the Moodle setup provided:
    # 19AI405 -> Assignment ID 4 (DEEP LEARNING)
    # 19AI411 -> Assignment ID 6 (NLP)
    # ML -> Assignment ID 2 (MACHINE LEARNING)
    
    mappings = [
        {
            "subject_code": "19AI405",
            "subject_name": "Deep Learning",
            "moodle_course_id": 3,
            "moodle_assignment_id": 4,
            "exam_session": "2024-1",
            "is_active": True,
        },
        {
            "subject_code": "19AI411",
            "subject_name": "Natural Language Processing",
            "moodle_course_id": 4,
            "moodle_assignment_id": 6,
            "exam_session": "2024-1",
            "is_active": True,
        },
        {
            "subject_code": "ML",
            "subject_name": "Machine Learning",
            "moodle_course_id": 2,
            "moodle_assignment_id": 2,
            "exam_session": "2024-1",
            "is_active": True,
        },
    ]
    
    async with async_session_maker() as session:
        for mapping in mappings:
            # Check if mapping exists
            result = await session.execute(
                text("SELECT id FROM subject_mappings WHERE subject_code = :code"),
                {"code": mapping["subject_code"]}
            )
            existing = result.fetchone()
            
            if not existing:
                subject_mapping = SubjectMapping(**mapping)
                session.add(subject_mapping)
                print(f"✓ Created mapping: {mapping['subject_code']} -> Assignment {mapping['moodle_assignment_id']}")
            else:
                print(f"✓ Mapping already exists: {mapping['subject_code']}")
        
        await session.commit()


async def seed_system_config():
    """Seed system configuration."""
    configs = [
        {
            "key": "moodle_maintenance_mode",
            "value": "false",
            "description": "Whether Moodle is in maintenance mode",
        },
        {
            "key": "max_file_size_mb",
            "value": "50",
            "description": "Maximum file size in MB for uploads",
        },
        {
            "key": "allowed_extensions",
            "value": "pdf,jpg,jpeg,png",
            "description": "Comma-separated list of allowed file extensions",
        },
        {
            "key": "exam_session",
            "value": "2024-SPRING",
            "description": "Current examination session",
        },
    ]
    
    async with async_session_maker() as session:
        for config in configs:
            result = await session.execute(
                text("SELECT id FROM system_config WHERE key = :key"),
                {"key": config["key"]}
            )
            existing = result.fetchone()
            
            if not existing:
                sys_config = SystemConfig(**config)
                session.add(sys_config)
                print(f"✓ Created config: {config['key']} = {config['value']}")
            else:
                print(f"✓ Config already exists: {config['key']}")
        
        await session.commit()


async def verify_database():
    """Verify database connection and tables."""
    print("\nVerifying database connection...")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✓ Database connection successful!")
            
        # List all tables
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
            
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False
    
    return True


async def seed_sample_data():
    """Create a small sample artifact and associated audit logs for local testing."""
    async with async_session_maker() as session:
        # Create a sample artifact
        sample = ExaminationArtifact(
            raw_filename='sample_999999999999_DEMO.pdf',
            original_filename='999999999999_DEMO.pdf',
            file_blob_path='storage/sample/999999999999_DEMO.pdf',
            file_hash='deadbeefcafebabefeedfacecafebeef00000000000000000000000000000000',
            parsed_reg_no='999999999999',
            parsed_subject_code='DEMO',
            file_size_bytes=1024,
            mime_type='application/pdf',
            workflow_status='PENDING'
        )
        session.add(sample)
        await session.flush()

        # Create a sample report_issue audit log
        issue = AuditLog(
            action='report_issue',
            action_category='report',
            actor_type='student',
            actor_id='999999999999',
            actor_username='999999999999',
            artifact_id=sample.id,
            description='Sample report (for testing)',
            request_data={'notes': 'Sample report created by init_db'},
        )
        session.add(issue)
        await session.flush()

        # Optionally create a deleted log (commented out by default)
        # deleted = AuditLog(
        #     action='report_deleted',
        #     action_category='report',
        #     actor_type='student',
        #     actor_id='999999999999',
        #     actor_username='999999999999',
        #     artifact_id=sample.id,
        #     target_type='audit_log',
        #     target_id=str(issue.id),
        #     description='Sample withdrawn report'
        # )
        # session.add(deleted)

        await session.commit()
        print('✓ Seeded sample artifact and report_issue audit log (reg 999999999999)')


async def main(seed_samples: bool = False):
    """Main initialization function."""
    print("=" * 60)
    print("  Examination Middleware - Database Initialization")
    print("=" * 60)
    print()
    
    # Create tables
    await create_tables()
    print()
    
    # Seed data
    print("Seeding initial data...")
    await seed_staff_user()
    await seed_subject_mappings()
    await seed_system_config()
    if seed_samples:
        print("Seeding optional sample data...")
        await seed_sample_data()
    print()
    
    # Verify
    success = await verify_database()
    
    if success:
        print()
        print("=" * 60)
        print("  Database initialization completed successfully!")
        print("=" * 60)
        print()
        print("  You can now start the application with:")
        print("  python run.py")
        print()
    else:
        print()
        print("=" * 60)
        print("  Database initialization failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize database and seed data')
    parser.add_argument('--seed-samples', action='store_true', help='Seed sample artifacts and audit logs for local testing')
    args = parser.parse_args()

    asyncio.run(main(seed_samples=args.seed_samples))
