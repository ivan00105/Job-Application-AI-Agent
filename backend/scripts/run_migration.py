"""Database migration script to apply PostgreSQL schema"""
import asyncio
import asyncpg
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_settings
settings = get_settings()


async def run_migration():
    """Run the database migration"""
    print("Running database migration...\n")
    
    migration_file = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "20251005111019_create_initial_schema.sql"
    
    if not migration_file.exists():
        print(f"Migration file not found: {migration_file}")
        return False
    
    print(f"Reading migration file: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print(f"Connecting to PostgreSQL at {settings.postgres_host}:{settings.postgres_port}...")
    
    try:
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password
        )
        
        print("Connected to PostgreSQL\n")
        
        print("Executing migration SQL...")
        await conn.execute(migration_sql)
        
        print("Migration completed successfully\n")
        
        print("Verifying tables...")
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        expected_tables = ['users', 'cv_profiles', 'jobs', 'agent_memory', 'job_matches', 'applications']
        existing_tables = [row['tablename'] for row in tables]
        
        print("\nTables in database:")
        for table in existing_tables:
            status = "[OK]" if table in expected_tables else "[INFO]"
            print(f"  {status} {table}")
        
        missing_tables = set(expected_tables) - set(existing_tables)
        if missing_tables:
            print(f"\nMissing tables: {', '.join(missing_tables)}")
        else:
            print("\nAll expected tables created successfully")
        
        await conn.close()
        return True
        
    except asyncpg.PostgresError as e:
        print(f"\nPostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


async def main():
    """Main function"""
    print("=" * 60)
    print("  Job Application Agent - Database Migration")
    print("=" * 60 + "\n")
    
    success = await run_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("  Migration Complete")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Setup Qdrant collections: python scripts/setup_qdrant_collections.py")
        print("  2. Create test users: python scripts/create_test_users.py")
        print("  3. Start the backend: python main.py")
    else:
        print("\n" + "=" * 60)
        print("  Migration Failed")
        print("=" * 60)
        print("\nPlease check:")
        print("  1. PostgreSQL is running and accessible")
        print("  2. Database credentials in .env are correct")
        print("  3. Database exists")
        print("  4. User has necessary permissions")


if __name__ == "__main__":
    asyncio.run(main())
