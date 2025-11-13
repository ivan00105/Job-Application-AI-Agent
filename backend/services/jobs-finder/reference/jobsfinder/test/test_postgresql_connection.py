"""
Test script to verify PostgreSQL database connection.
Tests connection to PostgreSQL server at 192.168.0.105:5133 for database ai.jobsfinder
"""
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
DB_HOST = "pg.groture.com"
DB_PORT = 5433
DB_NAME = "ai.jobsfinder"  # Note: Database names typically don't have dots, might need adjustment
DB_USER = "ai.jobsfinder"  # Will prompt if not provided
DB_PASSWORD = "comp7607!Hku"  # Will prompt if not provided

def test_postgresql_connection(user=None, password=None):
    """Test PostgreSQL server connection."""
    print("=" * 80)
    print("Testing PostgreSQL Connection")
    print("=" * 80)
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"Database: {DB_NAME}")
    print()
    
    # Use defaults from module constants if not provided
    if not user:
        user = DB_USER
    if not password:
        password = DB_PASSWORD
    
    # Prompt for credentials if still not provided
    if not user:
        user = input("Enter PostgreSQL username (or press Enter to skip): ").strip() or None
    if not password and user:
        import getpass
        password = getpass.getpass("Enter PostgreSQL password (or press Enter to skip): ").strip() or None
    
    if not user or not password:
        print("⚠️  No credentials provided. Testing connection without authentication...")
        print("   (This will likely fail, but will show connection attempt)")
    
    try:
        # Build connection string
        conn_params = {
            'host': DB_HOST,
            'port': DB_PORT,
            'database': DB_NAME,
        }
        
        if user:
            conn_params['user'] = user
        if password:
            conn_params['password'] = password
        
        print(f"Attempting to connect...")
        print(f"   Connection parameters: host={DB_HOST}, port={DB_PORT}, database={DB_NAME}")
        if user:
            print(f"   User: {user}")
        
        # Try to connect
        conn = psycopg2.connect(**conn_params)
        
        print(f"✅ PostgreSQL connection successful!")
        print()
        
        # Get connection info
        print("Connection Information:")
        print(f"   Server version: {conn.server_version}")
        print(f"   Database: {conn.get_dsn_parameters()['dbname']}")
        print(f"   User: {conn.get_dsn_parameters().get('user', 'N/A')}")
        print()
        
        # Test basic query
        print("Testing basic query...")
        cursor = conn.cursor()
        
        # Get PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   PostgreSQL version: {version.split(',')[0]}")
        
        # Get current database
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()[0]
        print(f"   Current database: {current_db}")
        
        # Get current user
        cursor.execute("SELECT current_user;")
        current_user = cursor.fetchone()[0]
        print(f"   Current user: {current_user}")
        
        # List all databases (if permissions allow)
        print()
        print("Listing available databases...")
        try:
            cursor.execute("""
                SELECT datname 
                FROM pg_database 
                WHERE datistemplate = false 
                ORDER BY datname;
            """)
            databases = cursor.fetchall()
            print(f"   Found {len(databases)} database(s):")
            for db in databases:
                marker = " ← current" if db[0] == current_db else ""
                print(f"      - {db[0]}{marker}")
        except Exception as e:
            print(f"   ⚠️  Could not list databases: {str(e)}")
            print(f"      (This is normal if user doesn't have permission)")
        
        # List schemas in current database
        print()
        print("Listing schemas in current database...")
        try:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY schema_name;
            """)
            schemas = cursor.fetchall()
            print(f"   Found {len(schemas)} schema(s):")
            for schema in schemas:
                print(f"      - {schema[0]}")
        except Exception as e:
            print(f"   ⚠️  Could not list schemas: {str(e)}")
        
        # List tables in current database
        print()
        print("Listing tables in current database...")
        try:
            cursor.execute("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name;
            """)
            tables = cursor.fetchall()
            if tables:
                print(f"   Found {len(tables)} table(s):")
                for schema, table in tables:
                    print(f"      - {schema}.{table}")
            else:
                print("   No tables found in current database")
        except Exception as e:
            print(f"   ⚠️  Could not list tables: {str(e)}")
        
        # Test a simple query
        print()
        print("Testing simple SELECT query...")
        try:
            cursor.execute("SELECT 1 as test_value, 'Connection test successful' as message;")
            result = cursor.fetchone()
            print(f"   ✅ Query executed successfully")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   ❌ Query failed: {str(e)}")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 80)
        print("✅ All connection tests passed!")
        print("=" * 80)
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ PostgreSQL connection failed!")
        print(f"   Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print(f"   - Check if PostgreSQL server is running at {DB_HOST}:{DB_PORT}")
        print(f"   - Verify the database name '{DB_NAME}' is correct")
        print(f"   - Check if the server allows connections from your IP")
        print(f"   - Verify username and password are correct")
        print(f"   - Check PostgreSQL pg_hba.conf configuration")
        return False
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error occurred!")
        print(f"   Error: {str(e)}")
        print(f"   Error code: {e.pgcode if hasattr(e, 'pgcode') else 'N/A'}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error occurred!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_connection_without_database():
    """Test connection to PostgreSQL server without specifying a database."""
    print()
    print("=" * 80)
    print("Testing Connection to PostgreSQL Server (without database)")
    print("=" * 80)
    print()
    
    user = input("Enter PostgreSQL username (or press Enter to skip): ").strip() or None
    password = None
    if user:
        import getpass
        password = getpass.getpass("Enter PostgreSQL password (or press Enter to skip): ").strip() or None
    
    try:
        conn_params = {
            'host': DB_HOST,
            'port': DB_PORT,
        }
        
        if user:
            conn_params['user'] = user
        if password:
            conn_params['password'] = password
        
        # Connect to default 'postgres' database
        conn_params['database'] = 'postgres'
        
        print(f"Attempting to connect to 'postgres' database...")
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        print(f"✅ Connection to server successful!")
        
        cursor = conn.cursor()
        
        # List all databases
        print()
        print("Available databases:")
        cursor.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname;
        """)
        databases = cursor.fetchall()
        for db in databases:
            print(f"   - {db[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print()
    print("=" * 80)
    print("PostgreSQL Connection Test Script")
    print("=" * 80)
    print()
    print("This script will test the connection to PostgreSQL database.")
    print(f"Target: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print()
    
    # Test 1: Direct connection to specified database
    # Use credentials from module constants
    success = test_postgresql_connection(user=DB_USER, password=DB_PASSWORD)
    
    if not success:
        print()
        response = input("Direct connection failed. Try connecting to server first? (yes/no): ").strip().lower()
        if response == 'yes':
            test_connection_without_database()
    
    print()
    print("=" * 80)
    print("Test completed!")
    print("=" * 80)
    print()
    print("Note: If database name contains a dot, it might be:")
    print("   - A schema.database format (unusual)")
    print("   - A database name that needs to be quoted")
    print("   - A typo (database names typically don't have dots)")
    print()
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

