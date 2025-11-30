"""Database migration script to add application status constraints"""
import asyncio
import asyncpg
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_settings

settings = get_settings()


async def run_status_migration():
    """Run the application status migration"""
    print("Running application status migration...\n")
    
    migration_file = Path(__file__).parent.parent.parent / "migrations" / "add_application_statuses.sql"
    
    if not migration_file.exists():
        print(f"Migration file not found: {migration_file}")
        return False
    
    print(f"Reading migration file: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
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
        
        print("Executing migration SQL...")
        await conn.execute(migration_sql)
        
        print("Migration completed successfully\n")
        
        # Verify the constraint was added
        constraint = await conn.fetchrow("""
            SELECT conname, pg_get_constraintdef(oid) as definition
            FROM pg_constraint 
            WHERE conname = 'applications_status_check'
        """)
        
        if constraint:
            print("✓ Status constraint verified:")
            print(f"  {constraint['definition']}")
        else:
            print("⚠ Warning: Could not verify constraint")
        
        await conn.close()
        return True
        
    except asyncpg.PostgresError as e:
        print(f"\nPostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    print("=" * 60)
    print("  Application Status Migration")
    print("=" * 60 + "\n")
    
    success = await run_status_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("  Migration Complete")
        print("=" * 60)
        print("\nApplication statuses are now available:")
        print("  - saved, applied, interviewing, offer, accepted")
        print("  - rejected, declined, withdrawn, not_interested")
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

