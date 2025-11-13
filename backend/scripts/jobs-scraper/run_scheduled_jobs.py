"""
Script to run job scraping based on schedules in job_schedules.csv

This script will:
1. Load schedules from backend/data/jobs/job_schedules.csv
2. Run scraping for each job immediately (not waiting for schedule)
3. Save results to PostgreSQL and Qdrant

Usage:
    python scripts/jobs-scraper/run_scheduled_jobs.py
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
from services.jobs_scraper.scheduler_config import load_schedules_from_csv

async def run_all_jobs():
    """Run all jobs from the CSV schedule file"""
    print("=" * 70)
    print("Job Scraping - Running All Scheduled Jobs")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load schedules from CSV
    csv_path = os.path.join(backend_dir, "data", "jobs", "job_schedules.csv")
    
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        return 1
    
    try:
        schedules = load_schedules_from_csv(csv_path)
        print(f"[INFO] Loaded {len(schedules)} jobs from CSV\n")
    except Exception as e:
        print(f"[ERROR] Failed to load CSV: {str(e)}")
        return 1
    
    # Initialize scraper
    scraper = JobScraperService()
    
    # Track overall statistics
    total_stats = {
        "total_jobs": len(schedules),
        "completed": 0,
        "total_scraped": 0,
        "total_saved": 0,
        "total_failed": 0,
        "total_qdrant_saved": 0
    }
    
    # Run each job
    for i, schedule in enumerate(schedules, 1):
        print("-" * 70)
        print(f"Job {i}/{len(schedules)}: {schedule.search_term} in {schedule.location}")
        print(f"  Target: {schedule.results_wanted} jobs")
        print("-" * 70)
        
        try:
            result = await scraper.scrape_and_save(
                search_term=schedule.search_term,
                location=schedule.location,
                results_wanted=schedule.results_wanted,
                hours_old=schedule.hours_old,
                sites=schedule.sites
            )
            
            # Update statistics
            total_stats["completed"] += 1
            total_stats["total_scraped"] += result.get("scraped", 0)
            total_stats["total_saved"] += result.get("saved", 0)
            total_stats["total_failed"] += result.get("failed", 0)
            total_stats["total_qdrant_saved"] += result.get("qdrant_saved", 0)
            
            # Print results
            print(f"\n  Results:")
            print(f"    Scraped: {result.get('scraped', 0)}")
            print(f"    Saved to PostgreSQL: {result.get('saved', 0)}")
            print(f"    Saved to Qdrant: {result.get('qdrant_saved', 0)}")
            print(f"    Failed: {result.get('failed', 0)}")
            
            if result.get('csv_file'):
                print(f"    CSV: {result.get('csv_file')}")
            
            success_rate = (result.get('saved', 0) / result.get('scraped', 1)) * 100 if result.get('scraped', 0) > 0 else 0
            print(f"    Success Rate: {success_rate:.1f}%")
            print()
            
        except Exception as e:
            print(f"\n  [ERROR] Failed to scrape {schedule.search_term}: {str(e)}")
            import traceback
            traceback.print_exc()
            total_stats["total_failed"] += schedule.results_wanted
            print()
    
    # Print summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total Jobs Scheduled: {total_stats['total_jobs']}")
    print(f"Completed: {total_stats['completed']}")
    print(f"Total Scraped: {total_stats['total_scraped']}")
    print(f"Total Saved to PostgreSQL: {total_stats['total_saved']}")
    print(f"Total Saved to Qdrant: {total_stats['total_qdrant_saved']}")
    print(f"Total Failed: {total_stats['total_failed']}")
    
    if total_stats['total_scraped'] > 0:
        overall_success = (total_stats['total_saved'] / total_stats['total_scraped']) * 100
        print(f"Overall Success Rate: {overall_success:.1f}%")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_jobs())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

