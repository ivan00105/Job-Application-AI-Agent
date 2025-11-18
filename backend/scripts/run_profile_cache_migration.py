"""
Run migration to create profile scoring cache and recommended jobs cache tables.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.postgres_client import get_postgres_client
from config import get_settings

async def run_migration():
    """Run the profile cache migration"""
    settings = get_settings()
    db = get_postgres_client()
    
    try:
        await db.connect()
        print("Connected to PostgreSQL")
        
        # Read migration file
        migration_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'migrations', 
            'create_profile_cache_tables.sql'
        )
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        print("Running migration...")
        await db.execute(migration_sql)
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        await db.disconnect()
        print("Disconnected from PostgreSQL")

if __name__ == "__main__":
    asyncio.run(run_migration())

