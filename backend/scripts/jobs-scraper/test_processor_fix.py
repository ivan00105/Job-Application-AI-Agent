"""
Quick test to verify the processor fix works
"""
import asyncio
import sys
import os

# Add paths for imports
backend_dir = os.path.dirname(__file__)
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

async def test_scraping():
    """Test scraping with a smaller number to verify fix"""
    print("=" * 60)
    print("Testing Processor Fix - Scraping 20 Finance Jobs")
    print("=" * 60)
    
    scraper = JobScraperService()
    
    try:
        result = await scraper.scrape_and_save(
            search_term="Finance Manager",
            location="Hong Kong",
            results_wanted=20,  # Smaller number for quick test
            hours_old=720,
            sites=None
        )
        
        print("\n" + "=" * 60)
        print("Results")
        print("=" * 60)
        print(f"Scraped: {result.get('scraped', 0)} jobs")
        print(f"Saved to PostgreSQL: {result.get('saved', 0)} jobs")
        print(f"Saved to Qdrant: {result.get('qdrant_saved', 0)} jobs")
        print(f"Failed: {result.get('failed', 0)} jobs")
        print(f"Skipped: {result.get('skipped', 0)} jobs")
        
        success_rate = (result.get('saved', 0) / result.get('scraped', 1)) * 100 if result.get('scraped', 0) > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if result.get('saved', 0) > 5:
            print("\n[SUCCESS] Fix appears to be working! More jobs are being saved.")
        elif result.get('saved', 0) > 0:
            print("\n[PARTIAL] Some jobs saved, but may need further investigation.")
        else:
            print("\n[WARNING] No jobs saved. Check logs for errors.")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_scraping())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted.")
        sys.exit(1)

