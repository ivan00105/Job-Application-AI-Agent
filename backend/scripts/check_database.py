"""
Check what data exists in the database.
Run this to see if jobs are already imported.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_db

def check_database():
    """Check database tables and counts"""
    db = get_db()
    
    print("=" * 60)
    print("DATABASE STATUS CHECK")
    print("=" * 60)
    
    # Check users
    try:
        users = db.table("users").select("*", count="exact").execute()
        print(f"\n✓ Users: {users.count} users found")
    except Exception as e:
        print(f"\n✗ Users table error: {e}")
    
    # Check jobs
    try:
        jobs = db.table("jobs").select("*", count="exact").execute()
        print(f"✓ Jobs: {jobs.count} jobs found")
        if jobs.count > 0:
            print(f"  - First job: {jobs.data[0].get('title', 'N/A')} at {jobs.data[0].get('company', 'N/A')}")
    except Exception as e:
        print(f"✗ Jobs table error: {e}")
    
    # Check CV profiles
    try:
        cvs = db.table("cv_profiles").select("*", count="exact").execute()
        print(f"✓ CV Profiles: {cvs.count} profiles found")
    except Exception as e:
        print(f"✗ CV Profiles table error: {e}")
    
    # Check applications
    try:
        apps = db.table("applications").select("*", count="exact").execute()
        print(f"✓ Applications: {apps.count} applications found")
    except Exception as e:
        print(f"✗ Applications table error: {e}")
    
    # Check interview questions
    try:
        questions = db.table("interview_questions").select("*", count="exact").execute()
        print(f"✓ Interview Questions: {questions.count} questions found")
    except Exception as e:
        print(f"✗ Interview Questions table error: {e}")
    
    print("\n" + "=" * 60)
    print("Database check complete!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    check_database()