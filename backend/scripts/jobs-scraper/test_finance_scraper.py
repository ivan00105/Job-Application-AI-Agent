"""
Test script to scrape finance/banking jobs in Hong Kong
This will run a single scraping job to test if it works
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

async def test_finance_scraping():
    """Test scraping finance jobs"""
    print("=" * 60)
    print("Testing Finance/Banking Job Scraping in Hong Kong")
    print("=" * 60)
    
    scraper = JobScraperService()
    
    # Test with Finance Manager jobs
    print("\n[TEST] Scraping Finance Manager jobs in Hong Kong...")
    print("Target: 100 jobs\n")
    
    try:
        result = await scraper.scrape_and_save(
            search_term="Finance Manager",
            location="Hong Kong",
            results_wanted=100,
            hours_old=720,
            sites=None  # Use all default sites
        )
        
        print("\n" + "=" * 60)
        print("Scraping Results")
        print("=" * 60)
        print(f"Search Term: Finance Manager")
        print(f"Location: Hong Kong")
        print(f"Scraped: {result.get('scraped', 0)} jobs")
        print(f"Saved to PostgreSQL: {result.get('saved', 0)} jobs")
        print(f"Saved to Qdrant: {result.get('qdrant_saved', 0)} jobs")
        print(f"Failed: {result.get('failed', 0)} jobs")
        print(f"Skipped: {result.get('skipped', 0)} jobs")
        
        if result.get('csv_file'):
            print(f"\nCSV File: {result.get('csv_file')}")
        
        print("\n" + "=" * 60)
        if result.get('saved', 0) > 0:
            print("[SUCCESS] Scraping completed successfully!")
        else:
            print("[WARNING] No jobs were saved. Check logs for details.")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Scraping failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_finance_scraping())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

