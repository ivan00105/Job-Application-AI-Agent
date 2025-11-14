"""
Script to purge all job data from PostgreSQL and Qdrant.
WARNING: This will delete ALL jobs from both databases!

Run from backend directory: python -m services.jobs_scraper.purge_all_data
Or from services/jobs-scraper: python purge_all_data.py
"""
import asyncio
import logging
import sys
import os

# Add paths for imports - adjust for new location
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
jobs_scraper_dir = os.path.dirname(__file__)
sys.path.insert(0, jobs_scraper_dir)
sys.path.insert(0, backend_dir)

# Create a mock package structure for relative imports
import importlib
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def purge_postgresql():
    """Delete all jobs from PostgreSQL"""
    print("\n" + "="*60)
    print("Purging PostgreSQL Database")
    print("="*60)
    
    try:
        db_service = DatabaseService()
        
        # Get connection
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Count existing jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        count = cursor.fetchone()[0]
        print(f"Found {count} jobs in PostgreSQL")
        
        if count == 0:
            print("[INFO] No jobs to delete in PostgreSQL")
            cursor.close()
            return 0
        
        # Confirm deletion
        print(f"\n[WARNING] This will delete ALL {count} jobs from PostgreSQL!")
        response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("[CANCELLED] PostgreSQL purge cancelled by user")
            cursor.close()
            return 0
        
        # Delete all jobs
        print("\nDeleting all jobs from PostgreSQL...")
        cursor.execute("DELETE FROM jobs")
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        
        print(f"[SUCCESS] Deleted {deleted_count} jobs from PostgreSQL")
        return deleted_count
        
    except Exception as e:
        print(f"[ERROR] Error purging PostgreSQL: {str(e)}")
        import traceback
        traceback.print_exc()
        return -1

def purge_qdrant():
    """Delete all data from Qdrant collection"""
    print("\n" + "="*60)
    print("Purging Qdrant Collection")
    print("="*60)
    
    try:
        qdrant_service = QdrantService()
        settings = get_scraper_settings()
        collection_name = settings.qdrant_collection_name
        
        # Check if collection exists
        if not qdrant_service.collection_exists(collection_name):
            print(f"[INFO] Collection '{collection_name}' does not exist in Qdrant")
            return 0
        
        # Get collection info
        collection_info = qdrant_service.get_collection_info(collection_name)
        if collection_info:
            points_count = collection_info['points_count']
            print(f"Found {points_count} points in collection '{collection_name}'")
        else:
            print(f"[INFO] Could not get collection info for '{collection_name}'")
            points_count = 0
        
        if points_count == 0:
            print("[INFO] No data to delete in Qdrant")
            return 0
        
        # Confirm deletion
        print(f"\n[WARNING] This will delete ALL {points_count} points from Qdrant collection '{collection_name}'!")
        response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("[CANCELLED] Qdrant purge cancelled by user")
            return 0
        
        # Delete collection (this deletes all data)
        print(f"\nDeleting collection '{collection_name}' from Qdrant...")
        qdrant_service.client.delete_collection(collection_name)
        
        # Recreate empty collection
        print(f"Recreating empty collection '{collection_name}'...")
        qdrant_service.create_collection(collection_name)
        
        print(f"[SUCCESS] Deleted all {points_count} points from Qdrant collection '{collection_name}'")
        return points_count
        
    except Exception as e:
        print(f"[ERROR] Error purging Qdrant: {str(e)}")
        import traceback
        traceback.print_exc()
        return -1

def main():
    """Main function to purge all data"""
    
    print("\n" + "="*60)
    print("DATA PURGE SCRIPT")
    print("="*60)
    print("\n[WARNING] This script will delete ALL job data from:")
    print("  - PostgreSQL (jobs table)")
    print("  - Qdrant (job_data collection)")
    print("\nThis action CANNOT be undone!")
    
    # Final confirmation
    print("\n" + "="*60)
    response = input("Type 'DELETE ALL' to confirm: ").strip()
    
    if response != 'DELETE ALL':
        print("\n[CANCELLED] Purge cancelled - confirmation text did not match")
        return 0
    
    # Purge PostgreSQL
    pg_count = purge_postgresql()
    
    # Purge Qdrant
    qdrant_count = purge_qdrant()
    
    # Summary
    print("\n" + "="*60)
    print("Purge Summary")
    print("="*60)
    if pg_count >= 0:
        print(f"PostgreSQL: Deleted {pg_count} jobs")
    else:
        print("PostgreSQL: Error occurred")
    
    if qdrant_count >= 0:
        print(f"Qdrant: Deleted {qdrant_count} points")
    else:
        print("Qdrant: Error occurred")
    
    if pg_count >= 0 and qdrant_count >= 0:
        print("\n[SUCCESS] All data purged successfully!")
    else:
        print("\n[WARNING] Some errors occurred during purge")
    
    print("="*60)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Purge interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

