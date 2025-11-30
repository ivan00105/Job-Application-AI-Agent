#!/usr/bin/env python3
"""
Script to apply the preparation tables migration to PostgreSQL.
Creates tables for tailored_cvs and cover_letters.
"""
import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings


async def run_migration():
    """Apply the preparation tables migration"""
    settings = get_settings()
    
    print("=" * 60)
    print("Application Preparation Tables Migration")
    print("=" * 60)
    print(f"Connecting to PostgreSQL at {settings.postgres_host}:{settings.postgres_port}...")
    
    try:
        # Use postgres_db if available, otherwise postgres_database
        db_name = settings.postgres_db or settings.postgres_database
        
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=db_name,
            user=settings.postgres_user,
            password=settings.postgres_password
        )
        
        print("Connected to PostgreSQL\n")
        
        # Read the migration file
        migration_file = Path(__file__).parent.parent.parent / "migrations" / "create_preparation_tables.sql"
        
        if not migration_file.exists():
            print(f"[ERROR] Migration file not found: {migration_file}")
            return False
        
        print(f"Reading migration file: {migration_file}")
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print("\nApplying migration...")
        print("-" * 60)
        
        # Execute the migration
        await conn.execute(migration_sql)
        
        print("-" * 60)
        print("[SUCCESS] Migration applied successfully!\n")
        
        # Verify tables were created
        print("Verifying tables...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('tailored_cvs', 'cover_letters')
            ORDER BY table_name
        """)
        
        if tables:
            print(f"✓ Found {len(tables)} table(s):")
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print("⚠ Warning: Tables not found after migration")
        
        # Check indexes
        indexes = await conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND (indexname LIKE 'idx_tailored_cvs%' OR indexname LIKE 'idx_cover_letters%')
            ORDER BY indexname
        """)
        
        if indexes:
            print(f"\n✓ Found {len(indexes)} index(es):")
            for idx in indexes:
                print(f"  - {idx['indexname']}")
        
        await conn.close()
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        return True
        
    except asyncpg.PostgresError as e:
        print(f"\n[ERROR] PostgreSQL error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your database connection settings in .env")
        print("  2. Ensure PostgreSQL is running and accessible")
        print("  3. Verify database name, user, and password are correct")
        print("  4. Make sure the database exists")
        return False
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_migration())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Migration cancelled by user")
        sys.exit(1)

