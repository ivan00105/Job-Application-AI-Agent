"""
API-friendly job scraping script that can be called via subprocess.
Accepts command-line arguments and outputs JSON results.
"""
import asyncio
import logging
import sys
import os
import json
import argparse

# Ensure UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    import io
    # Reconfigure stdout and stderr to use UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    # Set environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'

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

# Configure logging to stderr so stdout can be used for JSON output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Log to stderr, not stdout
)

logger = logging.getLogger(__name__)


async def scrape_jobs_async(
    search_term: str,
    location: str = "Hong Kong",
    results_wanted: int = 100,
    hours_old: int = 720,
    sites: list = None,
    country_indeed: str = None
):
    """Scrape jobs and return results as dictionary"""
    try:
        logger.info(f"Initializing JobScraperService for '{search_term}' in '{location}'...")
        scraper = JobScraperService()
        
        logger.info(f"Starting scraping: {results_wanted} jobs, max age: {hours_old} hours")
        result = await scraper.scrape_and_save(
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            sites=sites,
            country_indeed=country_indeed
        )
        
        logger.info(f"Scraping completed: {result.get('saved', 0)} jobs saved")
        return result
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "scraped": 0,
            "saved": 0,
            "failed": 0,
            "skipped": 0,
            "qdrant_saved": 0,
            "qdrant_failed": 0
        }


def main():
    """Main function - parses arguments and runs scraping"""
    parser = argparse.ArgumentParser(description='Scrape jobs from the internet')
    parser.add_argument('--search-term', required=True, help='Job search term')
    parser.add_argument('--location', default='Hong Kong', help='Job location')
    parser.add_argument('--results-wanted', type=int, default=100, help='Number of results to fetch')
    parser.add_argument('--hours-old', type=int, default=720, help='Maximum age of jobs in hours')
    parser.add_argument('--sites', help='Comma-separated list of sites (indeed,linkedin,google)')
    parser.add_argument('--country-indeed', help='Country for Indeed search')
    
    args = parser.parse_args()
    
    # Parse sites list
    sites_list = None
    if args.sites:
        sites_list = [s.strip() for s in args.sites.split(",") if s.strip()]
    
    try:
        # Run async scraping
        result = asyncio.run(scrape_jobs_async(
            search_term=args.search_term,
            location=args.location,
            results_wanted=args.results_wanted,
            hours_old=args.hours_old,
            sites=sites_list,
            country_indeed=args.country_indeed
        ))
        
        # Output JSON result to stdout (ensure UTF-8 encoding)
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        print(json_output, flush=True)
        
        # Exit with appropriate code
        if result.get('status') == 'error' or result.get('saved', 0) == 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        result = {
            "status": "error",
            "error": "Interrupted by user",
            "scraped": 0,
            "saved": 0,
            "failed": 0,
            "skipped": 0,
            "qdrant_saved": 0,
            "qdrant_failed": 0
        }
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        print(json_output, flush=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        result = {
            "status": "error",
            "error": str(e),
            "scraped": 0,
            "saved": 0,
            "failed": 0,
            "skipped": 0,
            "qdrant_saved": 0,
            "qdrant_failed": 0
        }
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        print(json_output, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

