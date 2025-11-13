"""
Test script to verify CSV scheduler loading
"""
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
from services.jobs_scraper.scheduler_config import load_schedules_from_csv, get_default_schedules

def test_csv_loading():
    """Test loading schedules from CSV"""
    csv_path = os.path.join(backend_dir, "data", "jobs", "job_schedules.csv")
    
    print("=" * 60)
    print("Testing CSV Scheduler Loading")
    print("=" * 60)
    
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        return 1
    
    try:
        # Test CSV loading
        print(f"\n[TEST] Loading schedules from CSV: {csv_path}")
        schedules = load_schedules_from_csv(csv_path)
        
        print(f"[OK] Successfully loaded {len(schedules)} schedules:\n")
        
        for i, schedule in enumerate(schedules, 1):
            print(f"  {i}. {schedule.search_term} in {schedule.location}")
            print(f"     - Schedule: {schedule.schedule_type}")
            if schedule.schedule_type == "cron":
                print(f"     - Time: {schedule.cron_hour}:{schedule.cron_minute:02d}")
                if schedule.cron_day_of_week:
                    print(f"     - Day: {schedule.cron_day_of_week}")
            elif schedule.schedule_type == "interval":
                print(f"     - Interval: Every {schedule.interval_hours} hours")
            print(f"     - Results: {schedule.results_wanted}")
            print(f"     - Hours old: {schedule.hours_old}")
            print()
        
        # Test get_default_schedules with CSV
        print("\n[TEST] Testing get_default_schedules with CSV...")
        csv_schedules = get_default_schedules(csv_path=csv_path)
        print(f"[OK] Loaded {len(csv_schedules)} schedules from CSV")
        
        # Test get_default_schedules with default path
        print("\n[TEST] Testing get_default_schedules with default path...")
        default_schedules = get_default_schedules()
        print(f"[OK] Loaded {len(default_schedules)} schedules from default CSV path")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = test_csv_loading()
    sys.exit(exit_code)

