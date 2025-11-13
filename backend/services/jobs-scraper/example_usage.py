"""
Example usage of the job scraping service.

This script demonstrates how to use the JobScraperService to scrape jobs
and save them to PostgreSQL and Qdrant.

Usage:
    cd backend
    python -m services.jobs_scraper.example_usage
"""
import asyncio
import logging
import sys
import os

# Add backend directory to path
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, backend_path)

# Import from the jobs-scraper module
from services.jobs_scraper.job_scraper_service import JobScraperService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main function to demonstrate job scraping"""
    
    # Initialize the service
    scraper = JobScraperService()
    
    # Example 1: Scrape Software Engineer jobs in Hong Kong
    print("\n" + "="*60)
    print("Example 1: Scraping Software Engineer jobs in Hong Kong")
    print("="*60)
    
    result = await scraper.scrape_and_save(
        search_term="Software Engineer",
        location="Hong Kong",
        results_wanted=50,  # Start with a small number for testing
        hours_old=720  # 30 days
    )
    
    print("\nResults:")
    print(f"  Scraped: {result['scraped']}")
    print(f"  Saved to PostgreSQL: {result['saved']}")
    print(f"  Skipped (duplicates): {result['skipped']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Saved to Qdrant: {result['qdrant_saved']}")
    print(f"  Qdrant failed: {result['qdrant_failed']}")
    
    # Example 2: Get collection info
    print("\n" + "="*60)
    print("Example 2: Qdrant Collection Information")
    print("="*60)
    
    collection_info = scraper.get_collection_info()
    if collection_info:
        print(f"Collection: {collection_info['name']}")
        print(f"Points: {collection_info['points_count']}")
        print(f"Vectors: {collection_info['vectors_count']}")
        print(f"Vector Size: {collection_info['config']['vector_size']}")
    else:
        print("Could not retrieve collection information")
    
    # Example 3: Scrape Data Analyst jobs
    print("\n" + "="*60)
    print("Example 3: Scraping Data Analyst jobs")
    print("="*60)
    
    result2 = await scraper.scrape_and_save(
        search_term="Data Analyst",
        location="Hong Kong",
        results_wanted=30,
        sites=["indeed", "linkedin"]  # Only scrape from specific sites
    )
    
    print("\nResults:")
    print(f"  Scraped: {result2['scraped']}")
    print(f"  Saved: {result2['saved']}")
    print(f"  Skipped: {result2['skipped']}")
    print(f"  Failed: {result2['failed']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()

