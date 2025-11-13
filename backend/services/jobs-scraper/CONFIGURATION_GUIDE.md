# Configuration Guide: Setting Search Terms and Locations

## Quick Start

Edit `scheduler_config.py` and modify the `get_default_schedules()` function.

## Basic Configuration

Each scraping job is defined using `ScrapingJobConfig`:

```python
ScrapingJobConfig(
    search_term="Software Engineer",  # ← Your job search term
    location="Hong Kong",              # ← Your location
    results_wanted=100,                # Number of jobs to scrape
    hours_old=720,                     # Jobs from last 30 days
    schedule_type="cron",             # "cron" or "interval"
    cron_hour=2,                      # Hour (0-23)
    cron_minute=0                     # Minute (0-59)
)
```

## Setting Search Term

The `search_term` is what you're searching for. Examples:

```python
search_term="Software Engineer"
search_term="Data Analyst"
search_term="Python Developer"
search_term="Machine Learning Engineer"
search_term="Full Stack Developer"
search_term="DevOps Engineer"
```

## Setting Location

The `location` is where to search for jobs. Examples:

```python
location="Hong Kong"
location="Singapore"
location="New York"
location="London"
location="Tokyo"
location="Sydney"
```

## Complete Examples

### Example 1: Daily Scraping at 2 AM
```python
ScrapingJobConfig(
    search_term="Software Engineer",
    location="Hong Kong",
    results_wanted=100,
    hours_old=720,
    schedule_type="cron",
    cron_hour=2,
    cron_minute=0
)
```

### Example 2: Every 6 Hours
```python
ScrapingJobConfig(
    search_term="Data Analyst",
    location="Singapore",
    results_wanted=50,
    schedule_type="interval",
    interval_hours=6
)
```

### Example 3: Multiple Locations
```python
# Hong Kong jobs
ScrapingJobConfig(
    search_term="Software Engineer",
    location="Hong Kong",
    schedule_type="cron",
    cron_hour=2,
    cron_minute=0
),

# Singapore jobs
ScrapingJobConfig(
    search_term="Software Engineer",
    location="Singapore",
    schedule_type="cron",
    cron_hour=3,
    cron_minute=0
),
```

### Example 4: Multiple Search Terms
```python
# Software Engineer
ScrapingJobConfig(
    search_term="Software Engineer",
    location="Hong Kong",
    schedule_type="cron",
    cron_hour=2,
    cron_minute=0
),

# Data Analyst
ScrapingJobConfig(
    search_term="Data Analyst",
    location="Hong Kong",
    schedule_type="cron",
    cron_hour=3,
    cron_minute=0
),
```

## Parameters Explained

| Parameter | Description | Example |
|-----------|-------------|---------|
| `search_term` | Job title/keywords to search | `"Software Engineer"` |
| `location` | Location to search jobs in | `"Hong Kong"` |
| `results_wanted` | Number of jobs to scrape | `100` |
| `hours_old` | Only jobs from last X hours | `720` (30 days) |
| `sites` | Which sites to scrape (optional) | `["indeed", "linkedin"]` |
| `schedule_type` | `"cron"` or `"interval"` | `"cron"` |
| `cron_hour` | Hour to run (0-23) | `2` (2 AM) |
| `cron_minute` | Minute to run (0-59) | `0` |
| `cron_day_of_week` | Day of week (optional) | `"mon"` (Mondays only) |
| `interval_hours` | Run every X hours | `12` (every 12 hours) |
| `interval_minutes` | Additional minutes | `30` |

## Step-by-Step: Adding a New Job

1. Open `scheduler_config.py`
2. Find the `get_default_schedules()` function
3. Add a new `ScrapingJobConfig` entry:

```python
ScrapingJobConfig(
    search_term="Your Job Title",     # ← Set your search term
    location="Your Location",         # ← Set your location
    results_wanted=100,
    hours_old=720,
    schedule_type="cron",
    cron_hour=2,
    cron_minute=0
),
```

4. Save the file
5. Restart the scheduler

## Common Search Terms

- `"Software Engineer"`
- `"Software Developer"`
- `"Full Stack Developer"`
- `"Backend Developer"`
- `"Frontend Developer"`
- `"Data Analyst"`
- `"Data Scientist"`
- `"Machine Learning Engineer"`
- `"DevOps Engineer"`
- `"Product Manager"`
- `"Business Analyst"`

## Common Locations

- `"Hong Kong"`
- `"Singapore"`
- `"New York"`
- `"London"`
- `"Tokyo"`
- `"Sydney"`
- `"San Francisco"`
- `"Toronto"`
- `"Berlin"`

## Tips

1. **Multiple Jobs**: You can add as many jobs as you want with different search terms and locations
2. **Same Search, Different Times**: Add multiple entries with the same search_term but different schedules
3. **Different Locations**: Search the same job title in different locations
4. **Test First**: Test with a small `results_wanted` first (e.g., 10) before scaling up

