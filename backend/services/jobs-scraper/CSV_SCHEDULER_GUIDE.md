# CSV-Based Scheduler Configuration Guide

## Overview

The scheduler can load scraping jobs from a CSV file, making it easy to manage many jobs without editing Python code.

## CSV File Location

Default location: `backend/data/jobs/job_schedules.csv`

You can specify a custom path when starting the scheduler.

## CSV Format

### Required Columns

- `search_term`: Job title/keywords to search for
- `location`: Location to search jobs in

### Optional Columns

- `results_wanted`: Number of jobs to scrape (default: 100)
- `hours_old`: Only jobs from last X hours (default: 720 = 30 days)
- `schedule_type`: `"cron"` or `"interval"` (default: `"cron"`)
- `cron_hour`: Hour to run (0-23) - for cron schedules
- `cron_minute`: Minute to run (0-59) - for cron schedules
- `cron_day_of_week`: Day of week (`"mon"`, `"tue"`, etc.) - for cron schedules
- `interval_hours`: Run every X hours - for interval schedules
- `interval_minutes`: Additional minutes - for interval schedules
- `sites`: Comma-separated list of sites (e.g., `"indeed,linkedin"`)

## Example CSV

```csv
search_term,location,results_wanted,hours_old,schedule_type,cron_hour,cron_minute,cron_day_of_week,interval_hours,interval_minutes
Software Engineer,Hong Kong,100,720,cron,2,0,,
Data Analyst,Hong Kong,50,720,interval,,,12,0
Data Scientist,Hong Kong,50,720,cron,9,0,mon,,
Python Developer,Singapore,100,720,cron,3,0,,
Machine Learning Engineer,New York,100,720,interval,,,6,0
```

## Schedule Types

### Cron Schedule (Specific Times)

For cron schedules, set:
- `schedule_type=cron`
- `cron_hour` (0-23)
- `cron_minute` (0-59)
- `cron_day_of_week` (optional: `"mon"`, `"tue"`, etc.)

Example:
```csv
search_term,location,schedule_type,cron_hour,cron_minute
Software Engineer,Hong Kong,cron,2,0
```

### Interval Schedule (Every X Hours)

For interval schedules, set:
- `schedule_type=interval`
- `interval_hours` (number of hours)
- `interval_minutes` (optional: additional minutes)

Example:
```csv
search_term,location,schedule_type,interval_hours,interval_minutes
Data Analyst,Hong Kong,interval,12,0
```

## Usage

### Automatic Detection

The scheduler automatically loads from `backend/data/jobs/job_schedules.csv`:

```bash
python services/jobs-scraper/scheduled_scraper.py
```

If the CSV file exists, it will be used. Otherwise, it falls back to hardcoded schedules.

### Custom CSV Path

You can modify `scheduled_scraper.py` to use a custom CSV path:

```python
scraper.add_default_jobs(use_csv=True, csv_path="/path/to/your/schedules.csv")
```

## CSV Examples

### Example 1: Daily Scraping at 2 AM

```csv
search_term,location,schedule_type,cron_hour,cron_minute
Software Engineer,Hong Kong,cron,2,0
Data Analyst,Singapore,cron,2,0
```

### Example 2: Every 6 Hours

```csv
search_term,location,schedule_type,interval_hours
Python Developer,Hong Kong,interval,6
Machine Learning Engineer,Singapore,interval,6
```

### Example 3: Weekly on Monday

```csv
search_term,location,schedule_type,cron_hour,cron_minute,cron_day_of_week
Data Scientist,Hong Kong,cron,9,0,mon
```

### Example 4: Multiple Locations

```csv
search_term,location,schedule_type,cron_hour,cron_minute
Software Engineer,Hong Kong,cron,2,0
Software Engineer,Singapore,cron,3,0
Software Engineer,New York,cron,4,0
```

### Example 5: With Custom Sites

```csv
search_term,location,sites,schedule_type,cron_hour,cron_minute
Software Engineer,Hong Kong,"indeed,linkedin",cron,2,0
Data Analyst,Singapore,"indeed,google",cron,3,0
```

## Tips

1. **Empty Fields**: Leave optional fields empty (blank) to use defaults
2. **Multiple Sites**: Use comma-separated values for `sites` column (e.g., `"indeed,linkedin"`)
3. **Day Names**: Use lowercase day abbreviations: `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`
4. **No Quotes Needed**: For simple text fields, quotes are optional (except for comma-separated values)
5. **Excel Compatible**: The CSV can be edited in Excel or Google Sheets

## Validation

The scheduler will:
- Check if CSV file exists
- Validate required columns (`search_term`, `location`)
- Use defaults for missing optional columns
- Log warnings for invalid values
- Fall back to hardcoded schedules if CSV loading fails

## Troubleshooting

### CSV Not Loading

- Check file path: `backend/data/jobs/job_schedules.csv`
- Verify CSV format (required columns present)
- Check for encoding issues (use UTF-8)
- Review logs for error messages

### Invalid Schedule

- Ensure `schedule_type` is either `"cron"` or `"interval"`
- For cron: provide `cron_hour` and `cron_minute`
- For interval: provide `interval_hours`

### Jobs Not Running

- Verify schedule times are correct
- Check if scheduler is running
- Review `scheduled_scraper.log` for errors

