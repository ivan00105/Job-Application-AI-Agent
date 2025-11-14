"""
Script to identify and fix duplicate job_ids in Qdrant

This will help clean up duplicates and ensure consistency with PostgreSQL.
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
from collections import defaultdict

def analyze_and_fix_duplicates():
    """Analyze duplicates and optionally fix them"""
    print("=" * 70)
    print("Qdrant Duplicate Analysis and Fix")
    print("=" * 70)
    
    try:
        db_service = DatabaseService()
        qdrant_service = QdrantService()
        settings = get_scraper_settings()
        
        # Get PostgreSQL job IDs
        print("\n[1] Getting PostgreSQL job IDs...")
        with db_service._get_cursor() as cursor:
            cursor.execute("SELECT id FROM jobs")
            results = cursor.fetchall()
            pg_job_ids = set(str(row['id']) for row in results)
        print(f"    Found {len(pg_job_ids)} jobs in PostgreSQL")
        
        # Get all Qdrant points
        print("\n[2] Getting Qdrant points...")
        collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
        qdrant_count = collection_info.points_count
        
        scroll_result = qdrant_service.client.scroll(
            collection_name=settings.qdrant_collection_name,
            limit=qdrant_count,
            with_payload=True,
            with_vectors=False
        )
        
        # Group by job_id
        job_id_to_points = defaultdict(list)
        points_to_delete = []
        
        for point in scroll_result[0]:
            payload = point.payload
            if payload and 'job_id' in payload:
                job_id = str(payload['job_id'])
                job_id_to_points[job_id].append(point.id)
        
        print(f"    Found {len(job_id_to_points)} unique job_ids in {qdrant_count} points")
        
        # Find duplicates
        duplicates = {jid: point_ids for jid, point_ids in job_id_to_points.items() if len(point_ids) > 1}
        print(f"\n[3] Found {len(duplicates)} duplicate job_ids")
        
        if duplicates:
            print("\n    Sample duplicates:")
            for i, (job_id, point_ids) in enumerate(list(duplicates.items())[:5]):
                print(f"      {job_id}: {len(point_ids)} points")
                # Keep the first one, mark others for deletion
                points_to_delete.extend(point_ids[1:])
        
        # Find jobs in Qdrant but not in PostgreSQL
        qdrant_job_ids = set(job_id_to_points.keys())
        only_in_qdrant = qdrant_job_ids - pg_job_ids
        only_in_pg = pg_job_ids - qdrant_job_ids
        
        print(f"\n[4] Jobs only in Qdrant (not in PostgreSQL): {len(only_in_qdrant)}")
        print(f"    Jobs only in PostgreSQL (not in Qdrant): {len(only_in_pg)}")
        
        # Summary
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"PostgreSQL jobs: {len(pg_job_ids)}")
        print(f"Qdrant points: {qdrant_count}")
        print(f"Unique job_ids in Qdrant: {len(job_id_to_points)}")
        print(f"Duplicate job_ids: {len(duplicates)}")
        print(f"Points to delete (duplicates): {len(points_to_delete)}")
        print(f"Jobs in Qdrant but not PostgreSQL: {len(only_in_qdrant)}")
        
        # Ask if user wants to fix
        if points_to_delete or only_in_qdrant:
            print("\n" + "=" * 70)
            print("Fix Options")
            print("=" * 70)
            print("1. Delete duplicate points (keep first occurrence)")
            print("2. Delete jobs in Qdrant that don't exist in PostgreSQL")
            print("3. Both")
            print("4. Cancel")
            
            # For now, just show what would be deleted
            if points_to_delete:
                print(f"\nWould delete {len(points_to_delete)} duplicate points")
            if only_in_qdrant:
                print(f"Would delete {len(only_in_qdrant)} orphaned jobs from Qdrant")
                # Get point IDs for orphaned jobs
                orphaned_points = []
                for job_id in only_in_qdrant:
                    orphaned_points.extend(job_id_to_points[job_id])
                print(f"  ({len(orphaned_points)} points total)")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = analyze_and_fix_duplicates()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user.")
        sys.exit(1)

