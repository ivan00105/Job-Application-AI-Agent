"""Create test users for development"""
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
from passlib.context import CryptContext
from config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


async def create_test_users():
    """Create test user accounts in PostgreSQL"""
    
    test_users = [
        {"username": "testuser1", "password": "password123"},
        {"username": "testuser2", "password": "password123"},
        {"username": "testuser3", "password": "password123"},
        {"username": "demo", "password": "demo123"},
    ]

    print("Creating test users...\n")

    try:
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password
        )
        
        print(f"Connected to PostgreSQL at {settings.postgres_host}:{settings.postgres_port}\n")

        for user in test_users:
            # Check if user exists
            existing = await conn.fetchval(
                "SELECT id FROM users WHERE username = $1",
                user["username"]
            )

            if existing:
                print(f"User '{user['username']}' already exists (skipping)")
                continue

            # Hash password
            password_hash = pwd_context.hash(user["password"])

            # Insert user
            user_id = await conn.fetchval(
                "INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING id",
                user["username"],
                password_hash
            )

            print(f"Created user: {user['username']} (password: {user['password']})")

        await conn.close()

        print("\nTest users created successfully")
        print("\nYou can now login with:")
        for user in test_users:
            print(f"  Username: {user['username']}, Password: {user['password']}")
        
        return True

    except asyncpg.PostgresError as e:
        print(f"\nPostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"\nError: {e}")
        return False


async def main():
    """Main function"""
    print("=" * 60)
    print("  Job Application Agent - Create Test Users")
    print("=" * 60 + "\n")
    
    success = await create_test_users()
    
    if not success:
        print("\n" + "=" * 60)
        print("  Failed to Create Users")
        print("=" * 60)
        print("\nMake sure you have:")
        print("  1. Created .env file with PostgreSQL credentials")
        print("  2. Run database migration first: python scripts/run_migration.py")
        print("  3. Installed dependencies: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
