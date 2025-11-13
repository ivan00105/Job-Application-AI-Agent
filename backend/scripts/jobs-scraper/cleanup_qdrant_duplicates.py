"""
Script to clean up duplicate job_ids in Qdrant

This will delete duplicate points, keeping only the first occurrence of each job_id.
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

def cleanup_duplicates():
    """Clean up duplicate job_ids in Qdrant"""
    print("=" * 70)
    print("Qdrant Duplicate Cleanup")
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
        
        for point in scroll_result[0]:
            payload = point.payload
            if payload and 'job_id' in payload:
                job_id = str(payload['job_id'])
                job_id_to_points[job_id].append({
                    'point_id': point.id,
                    'payload': payload
                })
        
        print(f"    Found {len(job_id_to_points)} unique job_ids in {qdrant_count} points")
        
        # Find duplicates
        duplicates = {jid: points for jid, points in job_id_to_points.items() if len(points) > 1}
        print(f"\n[3] Found {len(duplicates)} duplicate job_ids")
        
        if not duplicates:
            print("\n✅ No duplicates found! Qdrant is clean.")
            return 0
        
        # Collect points to delete (keep first, delete rest)
        points_to_delete = []
        total_duplicates = 0
        
        for job_id, points in duplicates.items():
            # Sort by point_id to ensure consistent selection
            points.sort(key=lambda x: x['point_id'])
            # Keep first, delete rest
            for point in points[1:]:
                points_to_delete.append(point['point_id'])
                total_duplicates += 1
        
        print(f"    Will delete {total_duplicates} duplicate points")
        print(f"    Will keep {len(duplicates)} points (one per job_id)")
        
        # Confirm deletion
        print("\n" + "=" * 70)
        response = input(f"Delete {total_duplicates} duplicate points? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("Cancelled.")
            return 0
        
        # Delete duplicates in batches
        print(f"\n[4] Deleting {total_duplicates} duplicate points...")
        batch_size = 100
        deleted = 0
        
        for i in range(0, len(points_to_delete), batch_size):
            batch = points_to_delete[i:i + batch_size]
            try:
                qdrant_service.client.delete(
                    collection_name=settings.qdrant_collection_name,
                    points_selector=batch
                )
                deleted += len(batch)
                print(f"    Deleted {deleted}/{total_duplicates} points...")
            except Exception as e:
                print(f"    [ERROR] Failed to delete batch: {str(e)}")
        
        print(f"\n✅ Successfully deleted {deleted} duplicate points")
        
        # Verify
        print("\n[5] Verifying cleanup...")
        collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
        new_count = collection_info.points_count
        print(f"    Qdrant now has {new_count} points")
        print(f"    PostgreSQL has {len(pg_job_ids)} jobs")
        print(f"    Difference: {new_count - len(pg_job_ids)}")
        
        if new_count == len(pg_job_ids):
            print("\n✅ Perfect! Counts now match!")
        else:
            print(f"\n⚠️  Still a mismatch of {abs(new_count - len(pg_job_ids))} points")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = cleanup_duplicates()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user.")
        sys.exit(1)

