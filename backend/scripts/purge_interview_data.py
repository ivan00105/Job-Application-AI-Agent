#!/usr/bin/env python3
"""
Purge all interview sessions and results from the database.
This script deletes all interview data while keeping the question bank intact.

Usage:
    python scripts/purge_interview_data.py          # Interactive mode (asks for confirmation)
    python scripts/purge_interview_data.py --yes     # Non-interactive mode (auto-confirms)
"""
import asyncio
import asyncpg
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_settings

async def purge_interview_data(auto_confirm: bool = False):
    """Delete all interview sessions, responses, and analytics."""
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
        print("\n⚠️  WARNING: This will delete ALL interview sessions and results!")
        print("The interview_questions table (question bank) will NOT be deleted.\n")
        
        # Count existing records
        responses_count = await conn.fetchval("SELECT COUNT(*) FROM interview_responses")
        sessions_count = await conn.fetchval("SELECT COUNT(*) FROM interview_sessions")
        analytics_count = await conn.fetchval("SELECT COUNT(*) FROM interview_performance_analytics")
        
        print(f"Current data:")
        print(f"  - Interview responses: {responses_count}")
        print(f"  - Interview sessions: {sessions_count}")
        print(f"  - Performance analytics: {analytics_count}\n")
        
        if responses_count == 0 and sessions_count == 0 and analytics_count == 0:
            print("✅ No interview data to delete. Database is already clean.")
            await conn.close()
            return
        
        # Confirm deletion
        if not auto_confirm:
            confirm = input("Are you sure you want to delete all interview data? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Operation cancelled.")
                await conn.close()
                return
        else:
            print("Auto-confirming deletion (--yes flag provided)...")
        
        print("\nDeleting interview data...")
        
        # Delete in order to respect foreign key constraints
        # 1. Delete responses first (references sessions)
        if responses_count > 0:
            await conn.execute("DELETE FROM interview_responses")
            print(f"✅ Deleted {responses_count} interview responses")
        
        # 2. Delete sessions (references users and jobs)
        if sessions_count > 0:
            await conn.execute("DELETE FROM interview_sessions")
            print(f"✅ Deleted {sessions_count} interview sessions")
        
        # 3. Delete analytics (references users)
        if analytics_count > 0:
            await conn.execute("DELETE FROM interview_performance_analytics")
            print(f"✅ Deleted {analytics_count} performance analytics records")
        
        # Verify deletion
        remaining_responses = await conn.fetchval("SELECT COUNT(*) FROM interview_responses")
        remaining_sessions = await conn.fetchval("SELECT COUNT(*) FROM interview_sessions")
        remaining_analytics = await conn.fetchval("SELECT COUNT(*) FROM interview_performance_analytics")
        
        print("\n✅ Purge completed successfully!")
        print(f"\nRemaining data:")
        print(f"  - Interview responses: {remaining_responses}")
        print(f"  - Interview sessions: {remaining_sessions}")
        print(f"  - Performance analytics: {remaining_analytics}")
        print(f"  - Interview questions: {await conn.fetchval('SELECT COUNT(*) FROM interview_questions')} (preserved)")
        
    except Exception as e:
        print(f"❌ Error purging interview data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    asyncio.run(purge_interview_data(auto_confirm=auto_confirm))

