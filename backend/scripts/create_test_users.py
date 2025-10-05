"""
Create test users for development.
Run this script to populate database with test accounts.
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_db
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_users():
    """Create test user accounts"""
    db = get_db()

    test_users = [
        {"username": "testuser1", "password": "password123"},
        {"username": "testuser2", "password": "password123"},
        {"username": "demo", "password": "demo123"},
    ]

    print("Creating test users...")

    for user in test_users:
        # Check if user exists
        existing = db.table("users").select("id").eq("username", user["username"]).execute()

        if existing.data:
            print(f"❌ User '{user['username']}' already exists")
            continue

        # Hash password
        password_hash = pwd_context.hash(user["password"])

        # Insert user
        result = db.table("users").insert({
            "username": user["username"],
            "password_hash": password_hash
        }).execute()

        print(f"✅ Created user: {user['username']} (password: {user['password']})")

    print("\n🎉 Test users created successfully!")
    print("\nYou can now login with:")
    for user in test_users:
        print(f"  Username: {user['username']}, Password: {user['password']}")


if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with SUPABASE_URL and SUPABASE_KEY")
        print("2. Installed all dependencies: pip install -r requirements.txt")
        sys.exit(1)
