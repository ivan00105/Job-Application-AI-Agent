"""
Test script for the scheduled scraper.
This will start the scheduler and show the configured jobs.
Press Ctrl+C to stop.
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
from services.jobs_scraper.scheduled_scraper import ScheduledJobScraper

async def main():
    """Test the scheduler"""
    print("\n" + "="*60)
    print("Testing Scheduled Job Scraper")
    print("="*60)
    
    try:
        scraper = ScheduledJobScraper()
        
        # Add default jobs
        print("\nAdding scheduled jobs...")
        scraper.add_default_jobs()
        
        # Start scheduler
        scraper.start()
        
        print("\n[INFO] Scheduler is running. Jobs will execute according to schedule.")
        print("[INFO] Press Ctrl+C to stop the scheduler.")
        print("\nWaiting for scheduled jobs...")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute
                # Show next run times
                jobs = scraper.scheduler.get_jobs()
                if jobs:
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Active jobs: {len(jobs)}")
                    for job in jobs:
                        print(f"  - {job.id}: Next run at {job.next_run_time}")
        except KeyboardInterrupt:
            print("\n\n[INFO] Stopping scheduler...")
        finally:
            scraper.stop()
            print("[OK] Scheduler stopped")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    from datetime import datetime
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

