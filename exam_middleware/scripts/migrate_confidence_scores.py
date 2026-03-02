#!/usr/bin/env python3
"""
Migration Script: Add AI Extraction Confidence Score Columns
Purpose: Automatically add register_confidence and subject_confidence columns to examination_artifacts
Auto-execution: Run this before starting the application for the first time

Usage:
    python scripts/migrate_confidence_scores.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.core.config import Settings
from app.db.database import engine


async def check_columns_exist():
    """Check if confidence columns already exist"""
    async with engine.connect() as conn:
        inspector = inspect(conn.sync_engine)
        columns = [col['name'] for col in inspector.get_columns('examination_artifacts')]
        
        register_exists = 'register_confidence' in columns
        subject_exists = 'subject_confidence' in columns
        
        return register_exists, subject_exists


async def run_migration():
    """Execute the migration to add confidence score columns"""
    print("🔍 Checking for existing columns...")
    
    # Check if columns exist
    register_exists, subject_exists = await check_columns_exist()
    
    if register_exists and subject_exists:
        print("✅ Columns already exist! No migration needed.")
        return True
    
    print("📋 Running migration: Adding confidence score columns...")
    
    migration_sql = """
    -- Add AI extraction confidence score columns
    ALTER TABLE examination_artifacts
    ADD COLUMN IF NOT EXISTS register_confidence INTEGER DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS subject_confidence INTEGER DEFAULT NULL;
    
    -- Add comments explaining the fields
    COMMENT ON COLUMN examination_artifacts.register_confidence IS 'AI confidence score (0-100%) for register number extraction';
    COMMENT ON COLUMN examination_artifacts.subject_confidence IS 'AI confidence score (0-100%) for subject code extraction';
    """
    
    try:
        async with engine.begin() as conn:
            await conn.execute(text(migration_sql))
        
        print("✅ Migration SUCCESS!")
        print("📊 Added columns:")
        print("   - register_confidence: INTEGER (0-100%)")
        print("   - subject_confidence: INTEGER (0-100%)")
        print("\n✨ Staff portal can now display extraction confidence scores!")
        return True
        
    except Exception as e:
        print(f"❌ Migration FAILED: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify DATABASE_URL environment variable is set correctly")
        print("2. Check Neon connection string in config.py")
        print("3. Ensure you have permissions to modify the table")
        return False


async def main():
    """Main entry point"""
    settings = Settings()
    print(f"🔗 Database: {settings.postgres_db}")
    print(f"🏠 Host: {settings.postgres_host}")
    print()
    
    success = await run_migration()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
