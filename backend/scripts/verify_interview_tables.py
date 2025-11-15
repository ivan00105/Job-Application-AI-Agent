#!/usr/bin/env python3
"""
Script to verify that interview tables exist in PostgreSQL.
"""
import asyncio
import asyncpg
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings


async def verify_tables():
    """Verify interview tables exist and have correct structure"""
    settings = get_settings()
    
    print("=" * 60)
    print("Verifying Interview Tables in PostgreSQL")
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
        
        # Check if tables exist
        expected_tables = [
            'interview_sessions',
            'interview_questions',
            'interview_responses',
            'interview_performance_analytics'
        ]
        
        print("Checking tables...")
        print("-" * 60)
        
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('interview_sessions', 'interview_questions', 'interview_responses', 'interview_performance_analytics')
            ORDER BY table_name
        """)
        
        found_table_names = [t['table_name'] for t in tables]
        
        for table_name in expected_tables:
            if table_name in found_table_names:
                print(f"✓ {table_name} - EXISTS")
            else:
                print(f"✗ {table_name} - MISSING")
        
        if len(found_table_names) != len(expected_tables):
            print(f"\n⚠ Warning: Expected {len(expected_tables)} tables, found {len(found_table_names)}")
        
        # Check table structures
        print("\n" + "=" * 60)
        print("Checking table structures...")
        print("=" * 60)
        
        for table_name in found_table_names:
            print(f"\nTable: {table_name}")
            print("-" * 60)
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """, table_name)
            
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # Check indexes
        print("\n" + "=" * 60)
        print("Checking indexes...")
        print("=" * 60)
        
        indexes = await conn.fetch("""
            SELECT indexname, tablename
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND (indexname LIKE 'idx_interview_%' OR tablename IN ('interview_sessions', 'interview_questions', 'interview_responses', 'interview_performance_analytics'))
            ORDER BY tablename, indexname
        """)
        
        if indexes:
            current_table = None
            for idx in indexes:
                if idx['tablename'] != current_table:
                    if current_table is not None:
                        print()
                    print(f"\nTable: {idx['tablename']}")
                    current_table = idx['tablename']
                print(f"  ✓ {idx['indexname']}")
        else:
            print("⚠ No indexes found")
        
        # Check for foreign keys
        print("\n" + "=" * 60)
        print("Checking foreign key constraints...")
        print("=" * 60)
        
        fks = await conn.fetch("""
            SELECT
                tc.table_name, 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
            AND tc.table_name IN ('interview_sessions', 'interview_questions', 'interview_responses', 'interview_performance_analytics')
            ORDER BY tc.table_name, kcu.column_name
        """)
        
        if fks:
            current_table = None
            for fk in fks:
                if fk['table_name'] != current_table:
                    if current_table is not None:
                        print()
                    print(f"\nTable: {fk['table_name']}")
                    current_table = fk['table_name']
                print(f"  ✓ {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        else:
            print("⚠ No foreign keys found")
        
        # Count rows in each table
        print("\n" + "=" * 60)
        print("Row counts...")
        print("=" * 60)
        
        for table_name in found_table_names:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"  {table_name}: {count} row(s)")
        
        await conn.close()
        print("\n" + "=" * 60)
        print("Verification completed!")
        print("=" * 60)
        return True
        
    except asyncpg.PostgresError as e:
        print(f"\n[ERROR] PostgreSQL error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(verify_tables())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Verification cancelled by user")
        sys.exit(1)

