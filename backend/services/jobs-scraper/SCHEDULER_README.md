# Scheduled Job Scraper

A service to automatically scrape jobs on a schedule using APScheduler.

## Features

- **Flexible Scheduling**: Supports both interval-based and cron-based scheduling
- **Multiple Jobs**: Can run multiple scraping jobs with different schedules
- **Automatic Execution**: Runs in the background and executes scraping jobs automatically
- **Logging**: Comprehensive logging to file and console
- **Graceful Shutdown**: Handles signals for clean shutdown

## Installation

The scheduler requires `apscheduler`:

```bash
pip install apscheduler
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

## Configuration

Edit `scheduler_config.py` to configure your scraping schedules:

```python
def get_default_schedules() -> List[ScrapingJobConfig]:
    return [
        # Example: Daily at 2:00 AM
        ScrapingJobConfig(
            search_term="Software Engineer",
            location="Hong Kong",
            results_wanted=100,
            hours_old=720,
            schedule_type="cron",
            cron_hour=2,
            cron_minute=0
        ),
        
        # Example: Every 12 hours
        ScrapingJobConfig(
            search_term="Data Analyst",
            location="Hong Kong",
            results_wanted=50,
            schedule_type="interval",
            interval_hours=12
        ),
    ]
```

## Schedule Types

### Interval Scheduling

Run at regular intervals (e.g., every X hours):

```python
ScrapingJobConfig(
    search_term="Software Engineer",
    schedule_type="interval",
    interval_hours=6,      # Every 6 hours
    interval_minutes=30    # Optional: additional minutes
)
```

### Cron Scheduling

Run at specific times (like cron jobs):

```python
ScrapingJobConfig(
    search_term="Data Analyst",
    schedule_type="cron",
    cron_hour=2,           # 2 AM
    cron_minute=0,         # 0 minutes
    cron_day_of_week="mon" # Only on Mondays (optional)
)
```

**Cron Examples:**
- Daily at 2 AM: `cron_hour=2, cron_minute=0`
- Every Monday at 9 AM: `cron_hour=9, cron_minute=0, cron_day_of_week="mon"`
- Every weekday at 8 AM: `cron_hour=8, cron_minute=0, cron_day_of_week="mon-fri"`

## Usage

### Run from Backend Directory

```bash
# From backend directory
python services/jobs-scraper/scheduled_scraper.py
```

### Run as Module

```bash
# From backend directory
python -m services.jobs_scraper.scheduled_scraper
```

### Run in Background (Linux/Mac)

```bash
# Run in background
nohup python services/jobs-scraper/scheduled_scraper.py > scheduler.log 2>&1 &

# Check if running
ps aux | grep scheduled_scraper

# Stop
pkill -f scheduled_scraper
```

### Run as Windows Service

You can use tools like `nssm` (Non-Sucking Service Manager) to run it as a Windows service:

```bash
# Install nssm
# Download from https://nssm.cc/download

# Install service
nssm install JobScraperScheduler "C:\Python313\python.exe" "C:\cursor\Job-Application-AI-Agent\backend\services\jobs-scraper\scheduled_scraper.py"

# Start service
nssm start JobScraperScheduler

# Stop service
nssm stop JobScraperScheduler
```

## Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `scheduled_scraper.log` in the current directory

## Example Schedules

### Daily Scraping
```python
ScrapingJobConfig(
    search_term="Software Engineer",
    schedule_type="cron",
    cron_hour=2,    # 2 AM daily
    cron_minute=0
)
```

### Every 6 Hours
```python
ScrapingJobConfig(
    search_term="Data Analyst",
    schedule_type="interval",
    interval_hours=6
)
```

### Weekly on Monday
```python
ScrapingJobConfig(
    search_term="Data Scientist",
    schedule_type="cron",
    cron_hour=9,           # 9 AM
    cron_minute=0,
    cron_day_of_week="mon" # Only Mondays
)
```

### Multiple Times Per Day
```python
# Add multiple jobs with same search term but different times
ScrapingJobConfig(
    search_term="Software Engineer",
    schedule_type="cron",
    cron_hour=2,    # 2 AM
    cron_minute=0
),
ScrapingJobConfig(
    search_term="Software Engineer",
    schedule_type="cron",
    cron_hour=14,   # 2 PM
    cron_minute=0
)
```

## Stopping the Scheduler

Press `Ctrl+C` to gracefully stop the scheduler. It will:
1. Finish any running scraping jobs
2. Stop accepting new jobs
3. Shutdown cleanly

## Monitoring

The scheduler logs:
- When each job starts
- Scraping results (scraped, saved, failed counts)
- Next run times for each job
- Errors and exceptions

Check `scheduled_scraper.log` for detailed logs.

## Troubleshooting

### Scheduler Not Running
- Check if APScheduler is installed: `pip list | grep apscheduler`
- Check logs for errors: `tail -f scheduled_scraper.log`

### Jobs Not Executing
- Verify the schedule configuration in `scheduler_config.py`
- Check system time/timezone settings
- Review logs for job execution errors

### Overlapping Jobs
- The scheduler is configured with `max_instances=1` to prevent overlapping
- If a job is still running when the next one is scheduled, it will be skipped

## Advanced Configuration

You can also programmatically add jobs:

```python
from services.jobs_scraper.scheduled_scraper import ScheduledJobScraper

scraper = ScheduledJobScraper()

# Add a custom job
scraper.add_job(
    search_term="Python Developer",
    location="Hong Kong",
    results_wanted=50,
    schedule_type="interval",
    hours=6
)

scraper.start()
```

