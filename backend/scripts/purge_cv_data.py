#!/usr/bin/env python3
"""
Purge all CV profiles, tailored CVs, and cover letters from the database.
This script deletes all CV-related data.

Usage:
    python scripts/purge_cv_data.py          # Interactive mode (asks for confirmation)
    python scripts/purge_cv_data.py --yes     # Non-interactive mode (auto-confirms)
"""
import asyncio
import asyncpg
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_settings

async def purge_cv_data(auto_confirm: bool = False):
    """Delete all CV profiles, tailored CVs, and cover letters."""
    settings = get_settings()
    db_name = settings.postgres_db or settings.postgres_database
    
    print("Connecting to PostgreSQL database...")
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=db_name,
        user=settings.postgres_user,
        password=settings.postgres_password
    )
    
    try:
        print("\n⚠️  WARNING: This will delete ALL CV-related data!")
        print("This includes:")
        print("  - All CV profiles (raw_text, parsed_data)")
        print("  - All tailored CVs (HTML/PDF content)")
        print("  - All cover letters\n")
        
        # Count existing records
        cv_profiles_count = await conn.fetchval("SELECT COUNT(*) FROM cv_profiles")
        tailored_cvs_count = await conn.fetchval("SELECT COUNT(*) FROM tailored_cvs")
        cover_letters_count = await conn.fetchval("SELECT COUNT(*) FROM cover_letters")
        
        print(f"Current data:")
        print(f"  - CV profiles: {cv_profiles_count}")
        print(f"  - Tailored CVs: {tailored_cvs_count}")
        print(f"  - Cover letters: {cover_letters_count}\n")
        
        if cv_profiles_count == 0 and tailored_cvs_count == 0 and cover_letters_count == 0:
            print("✅ No CV data to delete. Database is already clean.")
            await conn.close()
            return
        
        # Confirm deletion
        if not auto_confirm:
            confirm = input("Are you sure you want to delete all CV data? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Operation cancelled.")
                await conn.close()
                return
        else:
            print("Auto-confirming deletion (--yes flag provided)...")
        
        print("\nDeleting CV data...")
        
        # Delete in order to respect foreign key constraints
        # 1. Delete tailored CVs first (references cv_profiles)
        if tailored_cvs_count > 0:
            await conn.execute("DELETE FROM tailored_cvs")
            print(f"✅ Deleted {tailored_cvs_count} tailored CVs")
        
        # 2. Delete cover letters (references users and jobs, but independent)
        if cover_letters_count > 0:
            await conn.execute("DELETE FROM cover_letters")
            print(f"✅ Deleted {cover_letters_count} cover letters")
        
        # 3. Delete CV profiles (references users)
        if cv_profiles_count > 0:
            await conn.execute("DELETE FROM cv_profiles")
            print(f"✅ Deleted {cv_profiles_count} CV profiles")
        
        # Verify deletion
        remaining_profiles = await conn.fetchval("SELECT COUNT(*) FROM cv_profiles")
        remaining_tailored = await conn.fetchval("SELECT COUNT(*) FROM tailored_cvs")
        remaining_letters = await conn.fetchval("SELECT COUNT(*) FROM cover_letters")
        
        print("\n✅ Purge completed successfully!")
        print(f"\nRemaining data:")
        print(f"  - CV profiles: {remaining_profiles}")
        print(f"  - Tailored CVs: {remaining_tailored}")
        print(f"  - Cover letters: {remaining_letters}")
        
    except Exception as e:
        print(f"❌ Error purging CV data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    asyncio.run(purge_cv_data(auto_confirm=auto_confirm))

