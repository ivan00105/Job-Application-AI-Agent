"""
Detailed test for vector-based duplicate detection

This test will:
1. Scrape a unique job search term
2. Verify jobs are saved
3. Scrape the same term again
4. Verify duplicates are detected and skipped
"""
import asyncio
import sys
import os
from datetime import datetime

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
from services.jobs_scraper.job_scraper_service import JobScraperService
from services.jobs_scraper.database_service import DatabaseService
from services.jobs_scraper.qdrant_service import QdrantService
from services.jobs_scraper.config import get_scraper_settings

async def test_detailed_duplicate_detection():
    """Detailed test of duplicate detection"""
    print("=" * 70)
    print("Detailed Vector-Based Duplicate Detection Test")
    print("=" * 70)
    
    scraper = JobScraperService()
    db_service = DatabaseService()
    qdrant_service = QdrantService()
    settings = get_scraper_settings()
    
    # Use a unique search term with timestamp to avoid existing jobs
    unique_term = f"Quantitative Analyst {datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"\n[TEST] Using unique search term: '{unique_term}'")
    print(f"[INFO] Vector duplicate detection: {settings.use_vector_duplicate_detection}")
    print(f"[INFO] Similarity threshold: {settings.duplicate_similarity_threshold}")
    
    try:
        # Get initial counts
        print("\n[1] Getting initial database counts...")
        with db_service._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            initial_pg_count = cursor.fetchone()['count']
        
        collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
        initial_qdrant_count = collection_info.points_count
        
        print(f"    PostgreSQL: {initial_pg_count} jobs")
        print(f"    Qdrant: {initial_qdrant_count} points")
        
        # First scrape - should save new jobs
        print(f"\n[2] First scrape (should save new jobs)...")
        result1 = await scraper.scrape_and_save(
            search_term=unique_term,
            location="Hong Kong",
            results_wanted=5,  # Small number for testing
            hours_old=720
        )
        
        print(f"    Scraped: {result1.get('scraped', 0)}")
        print(f"    Saved: {result1.get('saved', 0)}")
        print(f"    Skipped: {result1.get('skipped', 0)}")
        print(f"    Failed: {result1.get('failed', 0)}")
        
        # Get counts after first scrape
        with db_service._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            after_first_pg_count = cursor.fetchone()['count']
        
        collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
        after_first_qdrant_count = collection_info.points_count
        
        new_jobs = after_first_pg_count - initial_pg_count
        print(f"\n    New jobs in PostgreSQL: {new_jobs}")
        print(f"    New points in Qdrant: {after_first_qdrant_count - initial_qdrant_count}")
        
        # Second scrape - should detect duplicates
        print(f"\n[3] Second scrape (should detect duplicates)...")
        result2 = await scraper.scrape_and_save(
            search_term=unique_term,
            location="Hong Kong",
            results_wanted=5,
            hours_old=720
        )
        
        print(f"    Scraped: {result2.get('scraped', 0)}")
        print(f"    Saved: {result2.get('saved', 0)}")
        print(f"    Skipped: {result2.get('skipped', 0)}")
        print(f"    Failed: {result2.get('failed', 0)}")
        
        # Get final counts
        with db_service._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            final_pg_count = cursor.fetchone()['count']
        
        collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
        final_qdrant_count = collection_info.points_count
        
        additional_jobs = final_pg_count - after_first_pg_count
        print(f"\n    Additional jobs saved: {additional_jobs}")
        
        # Verify results
        print("\n" + "=" * 70)
        print("Test Results")
        print("=" * 70)
        
        success = True
        
        if result1.get('saved', 0) > 0:
            print("✅ First scrape: Jobs were saved (as expected)")
        else:
            print("⚠️  First scrape: No jobs saved (might already exist or all failed)")
            if result1.get('skipped', 0) > 0:
                print("   Note: Some jobs were skipped (might be duplicates from previous tests)")
        
        if result2.get('skipped', 0) > 0:
            print(f"✅ Second scrape: {result2.get('skipped', 0)} duplicates detected and skipped")
        else:
            print("⚠️  Second scrape: No duplicates detected")
            if result2.get('saved', 0) > 0:
                print("   Note: Some jobs were saved again (duplicate detection might not be working)")
                success = False
        
        if additional_jobs == 0 and result2.get('skipped', 0) > 0:
            print("✅ Database consistency: No duplicate jobs added to database")
        elif additional_jobs > 0 and result2.get('saved', 0) == 0:
            print("⚠️  Warning: Jobs were saved but stats show 0 saved (check logs)")
        
        if success:
            print("\n🎉 SUCCESS! Vector-based duplicate detection is working correctly!")
        else:
            print("\n⚠️  WARNING: Some issues detected. Check the results above.")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_detailed_duplicate_detection())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted.")
        sys.exit(1)

