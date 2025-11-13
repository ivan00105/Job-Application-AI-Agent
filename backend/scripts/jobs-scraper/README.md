# Job Scraper Scripts

Scripts for running job scraping operations.

## Scripts

### 1. `run_scheduled_jobs.py`

Run all jobs from `job_schedules.csv` immediately (not waiting for schedule).

**Usage:**
```bash
python scripts/jobs-scraper/run_scheduled_jobs.py
```

**What it does:**
- Loads all jobs from `backend/data/jobs/job_schedules.csv`
- Runs scraping for each job immediately
- Saves results to PostgreSQL and Qdrant
- Generates CSV files with scraped data
- Shows summary statistics

**Example output:**
```
Job 1/5: Finance Manager in Hong Kong
  Target: 50 jobs
  Results:
    Scraped: 50
    Saved to PostgreSQL: 50
    Saved to Qdrant: 50
    Success Rate: 100.0%
```

### 2. `run_scheduler.py`

Start the scheduled job scraper service that runs jobs according to their schedules.

**Usage:**
```bash
python scripts/jobs-scraper/run_scheduler.py
```

**What it does:**
- Starts the scheduler service
- Loads jobs from `backend/data/jobs/job_schedules.csv`
- Executes jobs at their scheduled times (e.g., daily at 2 AM)
- Runs continuously until stopped (Ctrl+C)

## Configuration

Edit `backend/data/jobs/job_schedules.csv` to configure:
- Search terms
- Locations
- Number of jobs to scrape (`results_wanted`)
- Schedule times

## Examples

### Run all jobs immediately:
```bash
cd backend
python scripts/jobs-scraper/run_scheduled_jobs.py
```

### Start scheduler (runs on schedule):
```bash
cd backend
python scripts/jobs-scraper/run_scheduler.py
```

## Notes

- Make sure PostgreSQL and Qdrant are running
- Check `.env` file for database configuration
- CSV files are saved to `backend/data/jobs/` with timestamps

