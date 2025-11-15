#!/usr/bin/env python3
"""
Script to check if a specific interview session exists in the database.
"""
import asyncio
import asyncpg
import sys
from pathlib import Path
import uuid

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings


async def check_session(session_id: str):
    """Check if session exists and show details"""
    settings = get_settings()
    
    print("=" * 60)
    print(f"Checking Session: {session_id}")
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
        
        # Try to parse as UUID
        try:
            session_uuid = uuid.UUID(session_id)
            print(f"✓ Valid UUID format: {session_uuid}")
        except ValueError:
            print(f"✗ Invalid UUID format: {session_id}")
            await conn.close()
            return False
        
        # Check if session exists (without user_id check)
        print("\nChecking if session exists (any user)...")
        print("-" * 60)
        session_row = await conn.fetchrow(
            "SELECT id, user_id, status, domain, role_type, job_id, started_at, completed_at, completed_questions, total_questions, avg_score FROM interview_sessions WHERE id = $1",
            session_uuid
        )
        
        if session_row:
            print("✓ Session EXISTS in database")
            print(f"\nSession Details:")
            print(f"  ID: {session_row['id']}")
            print(f"  User ID: {session_row['user_id']}")
            print(f"  Status: {session_row['status']}")
            print(f"  Domain: {session_row['domain']}")
            print(f"  Role Type: {session_row['role_type']}")
            print(f"  Job ID: {session_row['job_id']}")
            print(f"  Started At: {session_row['started_at']}")
            print(f"  Completed At: {session_row['completed_at']}")
            print(f"  Progress: {session_row['completed_questions']}/{session_row['total_questions']}")
            print(f"  Avg Score: {session_row['avg_score']}")
            
            # Check responses
            response_count = await conn.fetchval(
                "SELECT COUNT(*) FROM interview_responses WHERE session_id = $1",
                session_uuid
            )
            print(f"\n  Responses: {response_count}")
            
        else:
            print("✗ Session NOT FOUND in database")
            print("\nChecking recent sessions...")
            recent_sessions = await conn.fetch(
                "SELECT id, user_id, status, started_at FROM interview_sessions ORDER BY started_at DESC LIMIT 5"
            )
            if recent_sessions:
                print("\nRecent sessions:")
                for sess in recent_sessions:
                    print(f"  - {sess['id']} (user: {sess['user_id']}, status: {sess['status']}, started: {sess['started_at']})")
            else:
                print("  No sessions found in database")
        
        await conn.close()
        print("\n" + "=" * 60)
        print("Check completed!")
        print("=" * 60)
        return session_row is not None
        
    except asyncpg.PostgresError as e:
        print(f"\n[ERROR] PostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_session.py <session_id>")
        sys.exit(1)
    
    session_id = sys.argv[1]
    try:
        success = asyncio.run(check_session(session_id))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Check cancelled by user")
        sys.exit(1)

