#!/usr/bin/env python3
"""Test session and question query together"""
import asyncio
import asyncpg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_settings

async def test():
    settings = get_settings()
    db_name = settings.postgres_db or settings.postgres_database
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=db_name,
        user=settings.postgres_user,
        password=settings.postgres_password
    )
    
    # Get the most recent session
    session = await conn.fetchrow("""
        SELECT * FROM interview_sessions 
        ORDER BY started_at DESC 
        LIMIT 1
    """)
    
    if not session:
        print("No sessions found")
        await conn.close()
        return
    
    print(f"Session found:")
    print(f"  ID: {session['id']}")
    print(f"  role_type: {session['role_type']}")
    print(f"  domain: {session['domain']}")
    print(f"  status: {session['status']}")
    print(f"  completed_questions: {session['completed_questions']}")
    print(f"  total_questions: {session['total_questions']}")
    
    # Get answered question IDs
    answered_rows = await conn.fetch(
        "SELECT question_id FROM interview_responses WHERE session_id = $1",
        session['id']
    )
    answered_ids = [r['question_id'] for r in answered_rows] if answered_rows else []
    print(f"\nAnswered question IDs: {len(answered_ids)}")
    
    # Build the query like the endpoint does
    conditions = ["is_active = TRUE"]
    params = []
    param_num = 1
    
    if session['role_type'] != "Both":
        conditions.append(f"(role_type = ${param_num} OR role_type = 'Both')")
        params.append(session['role_type'])
        param_num += 1
    
    if session['domain'] != "General":
        conditions.append(f"(domain = ${param_num} OR domain = 'General')")
        params.append(session['domain'])
        param_num += 1
    
    if answered_ids:
        conditions.append(f"id != ALL(${param_num}::uuid[])")
        params.append(answered_ids)
        param_num += 1
    
    query = f"SELECT * FROM interview_questions WHERE {' AND '.join(conditions)} LIMIT 1"
    
    print(f"\nQuery: {query}")
    print(f"Params: {params}")
    
    try:
        question = await conn.fetchrow(query, *params)
        if question:
            print(f"\n✓ Found question: {question['question_text'][:50]}...")
        else:
            print("\n✗ No question found")
    except Exception as e:
        print(f"\n✗ Query error: {e}")
        import traceback
        traceback.print_exc()
    
    await conn.close()

asyncio.run(test())

