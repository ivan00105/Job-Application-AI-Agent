"""
Script to scrape jobs and save to PostgreSQL and Qdrant.
Run from backend directory: python scrape_jobs.py
"""
import asyncio
import logging
import sys
import os

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
jobs_scraper_dir = os.path.join(backend_dir, "services", "jobs-scraper")
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
from services.jobs_scraper.job_scraper_service import JobScraperService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main function to scrape and save jobs"""
    
    print("\n" + "="*60)
    print("Job Scraping - Saving to PostgreSQL and Qdrant")
    print("="*60)
    
    try:
        # Initialize the service
        print("\nInitializing JobScraperService...")
        scraper = JobScraperService()
        print("[OK] Service initialized successfully")
        
        # Scrape 20 jobs
        print("\n" + "="*60)
        print("Scraping 20 Software Engineer jobs in Hong Kong")
        print("="*60)
        print("This may take a few minutes...")
        print()
        
        result = await scraper.scrape_and_save(
            search_term="Software Engineer",
            location="Hong Kong",
            results_wanted=20,
            hours_old=720
        )
        
        print("\n" + "="*60)
        print("Scraping Results")
        print("="*60)
        print(f"  Scraped: {result.get('scraped', 0)} jobs")
        print(f"  Saved to PostgreSQL: {result.get('saved', 0)} jobs")
        print(f"  Skipped (duplicates): {result.get('skipped', 0)} jobs")
        print(f"  Failed: {result.get('failed', 0)} jobs")
        print(f"  Saved to Qdrant: {result.get('qdrant_saved', 0)} jobs")
        print(f"  Qdrant failed: {result.get('qdrant_failed', 0)} jobs")
        
        if result.get('error'):
            print(f"\n  Error: {result.get('error')}")
        
        # Show CSV file info
        if result.get('csv_file'):
            print(f"\n  CSV File: {result.get('csv_file')}")
        
        # Get collection info
        print("\n" + "="*60)
        print("Qdrant Collection Information")
        print("="*60)
        collection_info = scraper.get_collection_info()
        if collection_info:
            print(f"Collection: {collection_info['name']}")
            print(f"Points: {collection_info['points_count']}")
            print(f"Vectors: {collection_info['vectors_count']}")
            print(f"Vector Size: {collection_info['config']['vector_size']}")
        else:
            print("Could not retrieve collection information")
        
        # Summary
        print("\n" + "="*60)
        if result.get('saved', 0) > 0:
            print(f"[SUCCESS] Successfully saved {result.get('saved', 0)} jobs to PostgreSQL")
        else:
            print("[WARNING] No jobs were saved to PostgreSQL")
            print("          Check PostgreSQL connection and server status")
        
        if result.get('qdrant_saved', 0) > 0:
            print(f"[SUCCESS] Successfully saved {result.get('qdrant_saved', 0)} jobs to Qdrant")
        else:
            print("[WARNING] No jobs were saved to Qdrant")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Scraping interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

