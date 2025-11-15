#!/usr/bin/env python3
"""Debug a specific interview session"""
import asyncio
import asyncpg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_settings

async def debug_session():
    session_id = "e9113eb7-1973-4d6d-b743-22bee0ba4ac3"
    settings = get_settings()
    db_name = settings.postgres_db or settings.postgres_database
    
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=db_name,
        user=settings.postgres_user,
        password=settings.postgres_password
    )
    
    print(f"Debugging session: {session_id}\n")
    print("=" * 60)
    
    # Get session
    session = await conn.fetchrow("""
        SELECT * FROM interview_sessions WHERE id = $1
    """, session_id)
    
    if not session:
        print("❌ Session not found!")
        await conn.close()
        return
    
    print("Session details:")
    print(f"  ID: {session['id']}")
    print(f"  user_id: {session['user_id']}")
    print(f"  role_type: {session['role_type']}")
    print(f"  domain: {session['domain']}")
    print(f"  status: {session['status']}")
    print(f"  completed_questions: {session['completed_questions']}")
    print(f"  total_questions: {session['total_questions']}")
    print(f"  job_id: {session['job_id']}")
    
    # Get answered questions
    answered = await conn.fetch("""
        SELECT question_id FROM interview_responses WHERE session_id = $1
    """, session_id)
    answered_ids = [r['question_id'] for r in answered]
    print(f"\nAnswered question IDs: {len(answered_ids)}")
    for aid in answered_ids:
        print(f"  - {aid}")
    
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
    
    print(f"\nQuery:")
    print(f"  {query}")
    print(f"\nParams:")
    for i, p in enumerate(params, 1):
        print(f"  ${i}: {p}")
    
    # Check available questions without filters
    all_questions = await conn.fetch("""
        SELECT id, domain, role_type, question_text 
        FROM interview_questions 
        WHERE is_active = TRUE
        LIMIT 10
    """)
    print(f"\nAvailable questions (first 10): {len(all_questions)}")
    for q in all_questions:
        print(f"  - {q['domain']}/{q['role_type']}: {q['question_text'][:50]}...")
    
    # Try the actual query
    try:
        result = await conn.fetchrow(query, *params)
        if result:
            print(f"\n✅ Query successful! Found question:")
            print(f"  ID: {result['id']}")
            print(f"  Text: {result['question_text'][:100]}...")
        else:
            print(f"\n❌ Query returned no results")
            
            # Check why - test each condition
            print("\nDebugging conditions:")
            
            # Test role_type filter
            role_test = await conn.fetch("""
                SELECT COUNT(*) as count FROM interview_questions 
                WHERE is_active = TRUE 
                AND (role_type = $1 OR role_type = 'Both')
            """, session['role_type'])
            print(f"  Questions matching role_type '{session['role_type']}': {role_test[0]['count']}")
            
            # Test domain filter
            domain_test = await conn.fetch("""
                SELECT COUNT(*) as count FROM interview_questions 
                WHERE is_active = TRUE 
                AND (domain = $1 OR domain = 'General')
            """, session['domain'])
            print(f"  Questions matching domain '{session['domain']}': {domain_test[0]['count']}")
            
            # Test combined
            combined_test = await conn.fetch("""
                SELECT COUNT(*) as count FROM interview_questions 
                WHERE is_active = TRUE 
                AND (role_type = $1 OR role_type = 'Both')
                AND (domain = $2 OR domain = 'General')
            """, session['role_type'], session['domain'])
            print(f"  Questions matching both: {combined_test[0]['count']}")
            
    except Exception as e:
        print(f"\n❌ Query error: {e}")
        import traceback
        traceback.print_exc()
    
    await conn.close()

asyncio.run(debug_session())

