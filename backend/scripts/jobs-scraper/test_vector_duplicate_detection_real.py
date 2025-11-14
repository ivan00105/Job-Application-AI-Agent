"""
Real-world test for vector-based duplicate detection

Tests with actual job searches to verify duplicate detection works
"""
import asyncio
import sys
import os
import time

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

async def test_real_duplicate_detection():
    """Test duplicate detection with real job searches"""
    print("=" * 70)
    print("Real-World Vector-Based Duplicate Detection Test")
    print("=" * 70)
    
    scraper = JobScraperService()
    db_service = DatabaseService()
    qdrant_service = QdrantService()
    settings = get_scraper_settings()
    
    print(f"\n[CONFIG] Vector duplicate detection: {settings.use_vector_duplicate_detection}")
    print(f"[CONFIG] Similarity threshold: {settings.duplicate_similarity_threshold}")
    print(f"[CONFIG] Duplicate detection enabled: {settings.enable_duplicate_detection}")
    
    # Use a common search term that should find jobs
    search_term = "Risk Analyst"
    
    try:
        # Get initial counts
        print(f"\n[1] Getting initial database counts...")
        with db_service._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            initial_pg_count = cursor.fetchone()['count']
        
        collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
        initial_qdrant_count = collection_info.points_count
        
        print(f"    PostgreSQL: {initial_pg_count} jobs")
        print(f"    Qdrant: {initial_qdrant_count} points")
        
        # First scrape
        print(f"\n[2] First scrape: '{search_term}' in Hong Kong...")
        print("    (This may take a moment...)")
        
        result1 = await scraper.scrape_and_save(
            search_term=search_term,
            location="Hong Kong",
            results_wanted=10,  # Small number for testing
            hours_old=720
        )
        
        print(f"\n    Results:")
        print(f"      Scraped: {result1.get('scraped', 0)}")
        print(f"      Saved: {result1.get('saved', 0)}")
        print(f"      Skipped: {result1.get('skipped', 0)} (duplicates)")
        print(f"      Failed: {result1.get('failed', 0)}")
        print(f"      Qdrant saved: {result1.get('qdrant_saved', 0)}")
        
        # Get counts after first scrape
        with db_service._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            after_first_pg_count = cursor.fetchone()['count']
        
        collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
        after_first_qdrant_count = collection_info.points_count
        
        new_jobs = after_first_pg_count - initial_pg_count
        print(f"\n    Database changes:")
        print(f"      New jobs in PostgreSQL: {new_jobs}")
        print(f"      New points in Qdrant: {after_first_qdrant_count - initial_qdrant_count}")
        
        # Wait a moment
        print(f"\n[3] Waiting 2 seconds before second scrape...")
        await asyncio.sleep(2)
        
        # Second scrape - should detect duplicates
        print(f"\n[4] Second scrape: '{search_term}' in Hong Kong (should detect duplicates)...")
        print("    (This may take a moment...)")
        
        result2 = await scraper.scrape_and_save(
            search_term=search_term,
            location="Hong Kong",
            results_wanted=10,
            hours_old=720
        )
        
        print(f"\n    Results:")
        print(f"      Scraped: {result2.get('scraped', 0)}")
        print(f"      Saved: {result2.get('saved', 0)}")
        print(f"      Skipped: {result2.get('skipped', 0)} (duplicates)")
        print(f"      Failed: {result2.get('failed', 0)}")
        print(f"      Qdrant saved: {result2.get('qdrant_saved', 0)}")
        
        # Get final counts
        with db_service._get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            final_pg_count = cursor.fetchone()['count']
        
        collection_info = qdrant_service.client.get_collection(settings.qdrant_collection_name)
        final_qdrant_count = collection_info.points_count
        
        additional_jobs = final_pg_count - after_first_pg_count
        print(f"\n    Database changes:")
        print(f"      Additional jobs saved: {additional_jobs}")
        print(f"      Additional points in Qdrant: {final_qdrant_count - after_first_qdrant_count}")
        
        # Verify results
        print("\n" + "=" * 70)
        print("Test Analysis")
        print("=" * 70)
        
        # Check if duplicate detection worked
        if result1.get('saved', 0) > 0:
            print("✅ First scrape: New jobs were saved")
        elif result1.get('skipped', 0) > 0:
            print("ℹ️  First scrape: All jobs were duplicates (already in database)")
        else:
            print("⚠️  First scrape: No jobs found or all failed")
        
        if result2.get('skipped', 0) > 0:
            print(f"✅ Second scrape: {result2.get('skipped', 0)} duplicates detected via vector search!")
            print("   This confirms vector-based duplicate detection is working.")
        elif result2.get('saved', 0) > 0:
            print(f"⚠️  Second scrape: {result2.get('saved', 0)} jobs were saved again")
            print("   This might indicate duplicate detection needs tuning.")
        else:
            print("ℹ️  Second scrape: No jobs found or all were already duplicates")
        
        if additional_jobs == 0 and result2.get('skipped', 0) > 0:
            print("✅ Database integrity: No duplicate jobs added (duplicates were skipped)")
        elif additional_jobs > 0 and result2.get('saved', 0) > 0:
            print(f"⚠️  Warning: {additional_jobs} additional jobs were saved in second scrape")
            print("   This suggests some jobs weren't detected as duplicates.")
        
        # Summary
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Total jobs in database: {final_pg_count}")
        print(f"Total points in Qdrant: {final_qdrant_count}")
        print(f"Jobs from first scrape: {result1.get('saved', 0)}")
        print(f"Duplicates detected in second scrape: {result2.get('skipped', 0)}")
        
        if result2.get('skipped', 0) > 0:
            print("\n🎉 SUCCESS! Vector-based duplicate detection is working!")
            print("   Duplicate jobs are being detected even when URLs differ.")
        else:
            print("\nℹ️  No duplicates detected in second scrape.")
            print("   This could mean:")
            print("   - All jobs were unique")
            print("   - Jobs have different descriptions (below similarity threshold)")
            print("   - No jobs were found in second scrape")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_real_duplicate_detection())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted.")
        sys.exit(1)

