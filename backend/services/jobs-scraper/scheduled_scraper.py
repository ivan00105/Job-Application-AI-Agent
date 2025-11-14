"""
Scheduled Job Scraper Service

Runs job scraping on a schedule. Can be configured via environment variables.
Supports multiple schedules and search terms.

Run from backend directory: python -m services.jobs_scraper.scheduled_scraper
Or as a service: python services/jobs-scraper/scheduled_scraper.py
"""
import asyncio
import logging
import sys
import os
import signal
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
jobs_scraper_dir = os.path.dirname(__file__)
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
from services.jobs_scraper.config import get_scraper_settings

# Try to import APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    print("[WARNING] APScheduler not installed. Install with: pip install apscheduler")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduled_scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ScheduledJobScraper:
    """Service to run job scraping on a schedule"""
    
    def __init__(self):
        if not APSCHEDULER_AVAILABLE:
            raise ImportError("APScheduler is required. Install with: pip install apscheduler")
        
        self.scheduler = AsyncIOScheduler()
        self.scraper = JobScraperService()
        self.settings = get_scraper_settings()
        self.running = False
        
    async def run_scraping_job(
        self,
        search_term: str,
        location: str = "Hong Kong",
        results_wanted: int = 100,
        hours_old: int = 720,
        sites: Optional[List[str]] = None
    ):
        """Run a single scraping job"""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled scraping: {search_term} in {location}")
        logger.info("=" * 60)
        
        try:
            result = await self.scraper.scrape_and_save(
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                sites=sites
            )
            
            logger.info("=" * 60)
            logger.info("Scheduled Scraping Complete")
            logger.info("=" * 60)
            logger.info(f"Search: {search_term} in {location}")
            logger.info(f"Scraped: {result.get('scraped', 0)}")
            logger.info(f"Saved to PostgreSQL: {result.get('saved', 0)}")
            logger.info(f"Saved to Qdrant: {result.get('qdrant_saved', 0)}")
            logger.info(f"Failed: {result.get('failed', 0)}")
            
            if result.get('csv_file'):
                logger.info(f"CSV saved: {result.get('csv_file')}")
            
        except Exception as e:
            logger.error(f"Error in scheduled scraping job: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def add_job(
        self,
        search_term: str,
        location: str = "Hong Kong",
        results_wanted: int = 100,
        hours_old: int = 720,
        sites: Optional[List[str]] = None,
        schedule_type: str = "interval",  # "interval" or "cron"
        **schedule_kwargs
    ):
        """
        Add a scheduled scraping job.
        
        Args:
            search_term: Job search term
            location: Job location
            results_wanted: Number of results to fetch
            hours_old: Maximum age of jobs in hours
            sites: List of sites to scrape
            schedule_type: "interval" or "cron"
            **schedule_kwargs: Schedule parameters
                For interval: hours, minutes, seconds
                For cron: hour, minute, day_of_week, etc.
        """
        job_id = f"scrape_{search_term}_{location}".replace(" ", "_").lower()
        
        if schedule_type == "interval":
            # Interval-based scheduling (e.g., every X hours)
            hours = schedule_kwargs.get('hours', 24)
            minutes = schedule_kwargs.get('minutes', 0)
            trigger = IntervalTrigger(hours=hours, minutes=minutes)
        elif schedule_type == "cron":
            # Cron-based scheduling (e.g., daily at specific time)
            trigger = CronTrigger(**schedule_kwargs)
        else:
            raise ValueError(f"Unknown schedule_type: {schedule_type}")
        
        self.scheduler.add_job(
            self.run_scraping_job,
            trigger=trigger,
            id=job_id,
            args=[search_term],
            kwargs={
                'location': location,
                'results_wanted': results_wanted,
                'hours_old': hours_old,
                'sites': sites
            },
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        
        logger.info(f"Added scheduled job: {job_id}")
        logger.info(f"  Search: {search_term} in {location}")
        logger.info(f"  Schedule: {schedule_type} - {trigger}")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.scheduler.start()
        self.running = True
        logger.info("=" * 60)
        logger.info("Scheduled Job Scraper Started")
        logger.info("=" * 60)
        logger.info(f"Active jobs: {len(self.scheduler.get_jobs())}")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.id}: Next run at {job.next_run_time}")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.scheduler.shutdown(wait=True)
        self.running = False
        logger.info("Scheduled Job Scraper Stopped")
    
    def add_default_jobs(self, csv_path: Optional[str] = None):
        """
        Add scraping jobs from CSV file.
        
        Args:
            csv_path: Path to CSV file (default: backend/data/jobs/job_schedules.csv)
        """
        # Import using absolute path to avoid relative import issues
        try:
            from .scheduler_config import get_default_schedules
        except ImportError:
            # Fallback for when running as script
            from services.jobs_scraper.scheduler_config import get_default_schedules
        
        schedules = get_default_schedules(csv_path=csv_path)
        
        for schedule in schedules:
            if schedule.schedule_type == "interval":
                self.add_job(
                    search_term=schedule.search_term,
                    location=schedule.location,
                    results_wanted=schedule.results_wanted,
                    hours_old=schedule.hours_old,
                    sites=schedule.sites,
                    schedule_type="interval",
                    hours=schedule.interval_hours or 24,
                    minutes=schedule.interval_minutes or 0
                )
            elif schedule.schedule_type == "cron":
                cron_kwargs = {}
                if schedule.cron_hour is not None:
                    cron_kwargs['hour'] = schedule.cron_hour
                if schedule.cron_minute is not None:
                    cron_kwargs['minute'] = schedule.cron_minute
                if schedule.cron_day_of_week:
                    cron_kwargs['day_of_week'] = schedule.cron_day_of_week
                
                self.add_job(
                    search_term=schedule.search_term,
                    location=schedule.location,
                    results_wanted=schedule.results_wanted,
                    hours_old=schedule.hours_old,
                    sites=schedule.sites,
                    schedule_type="cron",
                    **cron_kwargs
                )

def setup_signal_handlers(scraper: ScheduledJobScraper):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        scraper.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main function"""
    if not APSCHEDULER_AVAILABLE:
        print("[ERROR] APScheduler is required. Install with: pip install apscheduler")
        return 1
    
    scraper = ScheduledJobScraper()
    
    # Setup signal handlers
    setup_signal_handlers(scraper)
    
    # Load schedules from CSV file (required)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(backend_dir, "data", "jobs", "job_schedules.csv")
    
    logger.info(f"Loading schedules from CSV: {csv_path}")
    
    # Add scheduled jobs from CSV
    scraper.add_default_jobs(csv_path=csv_path)
    
    # Start scheduler
    scraper.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        scraper.stop()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

