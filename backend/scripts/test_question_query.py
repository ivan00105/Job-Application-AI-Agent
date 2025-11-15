#!/usr/bin/env python3
"""Test the question query logic"""
import asyncio
import asyncpg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_settings

async def test_query():
    settings = get_settings()
    db_name = settings.postgres_db or settings.postgres_database
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=db_name,
        user=settings.postgres_user,
        password=settings.postgres_password
    )
    
    # Test 1: Simple query with IT domain
    print("Test 1: IT domain, IT role_type")
    result = await conn.fetch("""
        SELECT * FROM interview_questions 
        WHERE is_active = TRUE 
        AND (role_type = $1 OR role_type = 'Both')
        AND (domain = $2 OR domain = 'General')
        LIMIT 1
    """, "IT", "IT")
    print(f"Found {len(result)} questions")
    if result:
        print(f"  Question: {result[0]['question_text'][:50]}...")
    
    # Test 2: Check what questions exist
    print("\nTest 2: All questions by domain and role_type")
    all_q = await conn.fetch("""
        SELECT domain, role_type, COUNT(*) as count
        FROM interview_questions
        WHERE is_active = TRUE
        GROUP BY domain, role_type
        ORDER BY domain, role_type
    """)
    for row in all_q:
        print(f"  {row['domain']} / {row['role_type']}: {row['count']}")
    
    # Test 3: Test with General domain
    print("\nTest 3: General domain")
    result = await conn.fetch("""
        SELECT * FROM interview_questions 
        WHERE is_active = TRUE 
        AND (role_type = $1 OR role_type = 'Both')
        LIMIT 1
    """, "IT")
    print(f"Found {len(result)} questions")
    
    await conn.close()

asyncio.run(test_query())

