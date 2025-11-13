"""
Simple PostgreSQL connection test script.
Usage:
    python test_postgresql_simple.py [username] [password]
    
Or set environment variables:
    export PGUSER=username
    export PGPASSWORD=password
"""
import sys
import os
import psycopg2
from psycopg2 import Error

# Database connection parameters
DB_HOST = "192.168.0.105"
DB_PORT = 5133
DB_NAME = "ai.jobsfinder"

def test_connection(username=None, password=None):
    """Test PostgreSQL connection with provided credentials."""
    # Get credentials from environment or arguments
    user = username or os.getenv('PGUSER')
    password = password or os.getenv('PGPASSWORD')
    
    print("=" * 80)
    print("PostgreSQL Connection Test")
    print("=" * 80)
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"Database: {DB_NAME}")
    if user:
        print(f"User: {user}")
    print()
    
    try:
        # Build connection parameters
        conn_params = {
            'host': DB_HOST,
            'port': DB_PORT,
            'database': DB_NAME,
        }
        
        if user:
            conn_params['user'] = user
        if password:
            conn_params['password'] = password
        
        print("Connecting to database...")
        conn = psycopg2.connect(**conn_params)
        
        print("✅ Connection successful!")
        print()
        
        # Get database info
        cursor = conn.cursor()
        
        # PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL Version: {version.split(',')[0]}")
        
        # Current database
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()[0]
        print(f"Current Database: {current_db}")
        
        # Current user
        cursor.execute("SELECT current_user;")
        current_user = cursor.fetchone()[0]
        print(f"Current User: {current_user}")
        
        # Test query
        cursor.execute("SELECT 1 as test;")
        result = cursor.fetchone()
        print(f"Test Query Result: {result[0]}")
        
        # List tables
        print()
        print("Tables in database:")
        cursor.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
            LIMIT 20;
        """)
        tables = cursor.fetchall()
        if tables:
            for schema, table in tables:
                print(f"  - {schema}.{table}")
        else:
            print("  (No tables found)")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 80)
        print("✅ All tests passed!")
        print("=" * 80)
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed!")
        print(f"Error: {str(e)}")
        print()
        print("Common issues:")
        print("  - Server not running or not accessible")
        print("  - Wrong host/port")
        print("  - Database name incorrect")
        print("  - Authentication failed (wrong username/password)")
        print("  - Firewall blocking connection")
        return False
        
    except Error as e:
        print(f"❌ PostgreSQL error: {str(e)}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    username = sys.argv[1] if len(sys.argv) > 1 else None
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not username:
        print("Usage: python test_postgresql_simple.py [username] [password]")
        print("Or set PGUSER and PGPASSWORD environment variables")
        print()
        username = input("Enter username (or press Enter to use environment): ").strip() or None
        if username:
            import getpass
            password = getpass.getpass("Enter password: ").strip() or None
    
    success = test_connection(username, password)
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted.")
        sys.exit(1)

