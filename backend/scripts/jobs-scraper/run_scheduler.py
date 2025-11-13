"""
Script to start the scheduled job scraper service

This will run the scheduler which will execute jobs according to their schedules
defined in backend/data/jobs/job_schedules.csv

Usage:
    python scripts/jobs-scraper/run_scheduler.py
"""
import sys
import os

# Add paths for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
scheduled_scraper_path = os.path.join(backend_dir, "services", "jobs-scraper", "scheduled_scraper.py")

# Change to backend directory
os.chdir(backend_dir)

# Run the scheduled scraper
if __name__ == "__main__":
    import subprocess
    try:
        # Run the scheduled scraper
        subprocess.run([sys.executable, scheduled_scraper_path], check=True)
    except KeyboardInterrupt:
        print("\n\n[INFO] Scheduler stopped by user.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Scheduler exited with error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

