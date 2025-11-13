"""
Script to check and compare job counts in PostgreSQL and Qdrant

This will help identify why the counts might be different.
"""
import sys
import os

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
jobs_scraper_dir = os.path.join(backend_dir, "services", "jobs-scraper")
sys.path.insert(0, jobs_scraper_dir)
sys.path.insert(0, backend_dir)

# Create a mock package structure for relative imports
import types

# Create a fake 'services.jobs_scraper' module
jobs_scraper_pkg = types.ModuleType('services')
jobs_scraper_subpkg = types.ModuleType('services.jobs_scraper')
sys.modules['services'] = jobs_scraper_pkg
sys.modules['services.jobs_scraper'] = jobs_scraper_subpkg
jobs_scraper_subpkg.__path__ = [jobs_scraper_dir]
jobs_scraper_subpkg.__file__ = os.path.join(jobs_scraper_dir, '__init__.py')

# Now import the modules
from services.jobs_scraper.database_service import DatabaseService
from services.jobs_scraper.qdrant_service import QdrantService
from services.jobs_scraper.config import get_scraper_settings

def check_counts():
    """Check job counts in both databases"""
    print("=" * 70)
    print("Database Count Comparison")
    print("=" * 70)
    
    try:
        # Initialize services
        db_service = DatabaseService()
        qdrant_service = QdrantService()
        settings = get_scraper_settings()
        
        # Get PostgreSQL count
        print("\n[1] Checking PostgreSQL...")
        try:
            # Query PostgreSQL directly
            with db_service._get_cursor() as cursor:
                cursor.execute("SELECT id FROM jobs")
                results = cursor.fetchall()
                pg_job_ids = [str(row['id']) for row in results]
                pg_count = len(pg_job_ids)
            print(f"    PostgreSQL jobs: {pg_count}")
        except Exception as e:
            print(f"    [ERROR] Failed to get PostgreSQL count: {str(e)}")
            import traceback
            traceback.print_exc()
            pg_count = 0
            pg_job_ids = []
        
        # Get Qdrant count
        print("\n[2] Checking Qdrant...")
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Get collection info
            collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
            qdrant_count = collection_info.points_count
            print(f"    Qdrant points: {qdrant_count}")
            
            # Get all point IDs from Qdrant
            scroll_result = qdrant_service.client.scroll(
                collection_name=settings.qdrant_collection_name,
                limit=qdrant_count,
                with_payload=True,
                with_vectors=False
            )
            qdrant_job_ids = []
            for point in scroll_result[0]:
                payload = point.payload
                if payload and 'job_id' in payload:
                    qdrant_job_ids.append(str(payload['job_id']))
            
            print(f"    Qdrant jobs with job_id: {len(qdrant_job_ids)}")
            
        except Exception as e:
            print(f"    [ERROR] Failed to get Qdrant count: {str(e)}")
            import traceback
            traceback.print_exc()
            qdrant_count = 0
            qdrant_job_ids = []
        
        # Compare counts
        print("\n" + "=" * 70)
        print("Comparison")
        print("=" * 70)
        print(f"PostgreSQL: {pg_count} jobs")
        print(f"Qdrant:     {qdrant_count} points ({len(qdrant_job_ids)} with job_id)")
        print(f"Difference: {pg_count - qdrant_count} jobs")
        
        if pg_count != qdrant_count:
            print("\n⚠️  MISMATCH DETECTED!")
            
            # Find jobs in PostgreSQL but not in Qdrant
            pg_set = set(pg_job_ids)
            qdrant_set = set(qdrant_job_ids)
            
            only_in_pg = pg_set - qdrant_set
            only_in_qdrant = qdrant_set - pg_set
            
            if only_in_pg:
                print(f"\n  Jobs in PostgreSQL but NOT in Qdrant: {len(only_in_pg)}")
                print(f"  Sample IDs: {list(only_in_pg)[:10]}")
            
            if only_in_qdrant:
                print(f"\n  Jobs in Qdrant but NOT in PostgreSQL: {len(only_in_qdrant)}")
                print(f"  Sample IDs: {list(only_in_qdrant)[:10]}")
            
            if not only_in_pg and not only_in_qdrant:
                print("\n  Note: Count mismatch but all job_ids match.")
                print("  This might be due to duplicate point IDs in Qdrant.")
        else:
            print("\n✅ Counts match!")
        
        # Additional analysis
        print("\n" + "=" * 70)
        print("Additional Analysis")
        print("=" * 70)
        
        # Check for duplicates in Qdrant (same job_id, different point_id)
        if qdrant_job_ids:
            from collections import Counter
            job_id_counts = Counter(qdrant_job_ids)
            duplicates = {jid: count for jid, count in job_id_counts.items() if count > 1}
            if duplicates:
                print(f"\n  Duplicate job_ids in Qdrant: {len(duplicates)}")
                print(f"  Sample: {dict(list(duplicates.items())[:5])}")
            else:
                print("\n  No duplicate job_ids found in Qdrant")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = check_counts()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user.")
        sys.exit(1)

