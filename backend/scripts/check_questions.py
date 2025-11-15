#!/usr/bin/env python3
"""Quick script to check question count"""
import asyncio
import asyncpg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_settings

async def check():
    settings = get_settings()
    db_name = settings.postgres_db or settings.postgres_database
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=db_name,
        user=settings.postgres_user,
        password=settings.postgres_password
    )
    count = await conn.fetchval("SELECT COUNT(*) FROM interview_questions")
    print(f"Total questions: {count}")
    
    by_domain = await conn.fetch("""
        SELECT domain, COUNT(*) as count 
        FROM interview_questions 
        GROUP BY domain
    """)
    print("\nBy domain:")
    for row in by_domain:
        print(f"  {row['domain']}: {row['count']}")
    
    await conn.close()

asyncio.run(check())

