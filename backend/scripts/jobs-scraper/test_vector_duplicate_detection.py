"""
Test script to verify vector-based duplicate detection works

This will test if the scraper can detect duplicate jobs even when URLs are different.
"""
import asyncio
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
from services.jobs_scraper.job_scraper_service import JobScraperService

async def test_duplicate_detection():
    """Test duplicate detection with vector search"""
    print("=" * 70)
    print("Testing Vector-Based Duplicate Detection")
    print("=" * 70)
    
    scraper = JobScraperService()
    
    print("\n[INFO] Scraping jobs...")
    print("This will test if duplicate jobs (same title/company, different URLs)")
    print("are detected using vector similarity search.\n")
    
    try:
        # Scrape a small batch first
        result1 = await scraper.scrape_and_save(
            search_term="Finance Manager",
            location="Hong Kong",
            results_wanted=10,
            hours_old=720
        )
        
        print(f"\n[1] First scrape:")
        print(f"    Scraped: {result1.get('scraped', 0)}")
        print(f"    Saved: {result1.get('saved', 0)}")
        print(f"    Skipped: {result1.get('skipped', 0)}")
        
        # Scrape again (should detect duplicates)
        print(f"\n[2] Second scrape (should detect duplicates):")
        result2 = await scraper.scrape_and_save(
            search_term="Finance Manager",
            location="Hong Kong",
            results_wanted=10,
            hours_old=720
        )
        
        print(f"    Scraped: {result2.get('scraped', 0)}")
        print(f"    Saved: {result2.get('saved', 0)}")
        print(f"    Skipped: {result2.get('skipped', 0)}")
        
        if result2.get('skipped', 0) > 0:
            print(f"\n✅ SUCCESS! Duplicate detection is working!")
            print(f"   {result2.get('skipped', 0)} duplicate jobs were detected and skipped.")
        else:
            print(f"\n⚠️  No duplicates detected. This could mean:")
            print(f"   - All jobs were unique")
            print(f"   - Similarity threshold might be too high")
            print(f"   - Jobs have different descriptions")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_duplicate_detection())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted.")
        sys.exit(1)

