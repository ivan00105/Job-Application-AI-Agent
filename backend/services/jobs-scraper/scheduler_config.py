"""
Configuration for scheduled job scraping.
Define your scraping schedules here or via environment variables.
Supports loading from CSV files.
"""
import os
import csv
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ScrapingJobConfig:
    """Configuration for a single scraping job"""
    search_term: str
    location: str = "Hong Kong"
    results_wanted: int = 100
    hours_old: int = 720
    sites: Optional[List[str]] = None
    
    # Schedule configuration
    schedule_type: str = "cron"  # "interval" or "cron"
    
    # For interval scheduling (e.g., every X hours)
    interval_hours: Optional[int] = None
    interval_minutes: Optional[int] = None
    
    # For cron scheduling (e.g., daily at specific time)
    cron_hour: Optional[int] = None  # 0-23
    cron_minute: Optional[int] = None  # 0-59
    cron_day_of_week: Optional[str] = None  # "mon", "tue", etc. or "*" for all days

def load_schedules_from_csv(csv_path: str) -> List[ScrapingJobConfig]:
    """
    Load scraping schedules from a CSV file.
    
    CSV Format:
    - Required columns: search_term, location
    - Optional columns: results_wanted, hours_old, schedule_type, 
                        cron_hour, cron_minute, cron_day_of_week,
                        interval_hours, interval_minutes, sites
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of ScrapingJobConfig objects
    """
    schedules = []
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_cols = ['search_term', 'location']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"CSV missing required columns: {missing_cols}")
        
        # Process each row
        for idx, row in df.iterrows():
            # Parse sites if present (comma-separated string or list)
            sites = None
            if 'sites' in df.columns and pd.notna(row.get('sites')):
                sites_str = str(row['sites']).strip()
                if sites_str:
                    sites = [s.strip() for s in sites_str.split(',')]
            
            # Helper function to safely convert to int, handling empty strings
            def safe_int(value, default=None):
                if pd.isna(value) or value == '' or str(value).strip() == '':
                    return default
                try:
                    return int(float(value))  # Handle float strings like "12.0"
                except (ValueError, TypeError):
                    return default
            
            config = ScrapingJobConfig(
                search_term=str(row['search_term']).strip(),
                location=str(row['location']).strip(),
                results_wanted=safe_int(row.get('results_wanted'), 100),
                hours_old=safe_int(row.get('hours_old'), 720),
                sites=sites,
                schedule_type=str(row.get('schedule_type', 'cron')).strip() if pd.notna(row.get('schedule_type')) and str(row.get('schedule_type')).strip() else 'cron',
                interval_hours=safe_int(row.get('interval_hours')),
                interval_minutes=safe_int(row.get('interval_minutes')),
                cron_hour=safe_int(row.get('cron_hour')),
                cron_minute=safe_int(row.get('cron_minute')),
                cron_day_of_week=str(row.get('cron_day_of_week')).strip() if pd.notna(row.get('cron_day_of_week')) and str(row.get('cron_day_of_week')).strip() else None,
            )
            schedules.append(config)
        
        return schedules
        
    except Exception as e:
        raise ValueError(f"Error reading CSV file {csv_path}: {str(e)}")


def get_default_schedules(csv_path: Optional[str] = None) -> List[ScrapingJobConfig]:
    """
    Get scraping schedules from CSV file.
    
    HOW TO SET SEARCH TERM AND LOCATION:
    - Edit the CSV file at backend/data/jobs/job_schedules.csv
    - Required columns: search_term, location
    - See CSV_SCHEDULER_GUIDE.md for format details
    
    Args:
        csv_path: Path to CSV file (default: backend/data/jobs/job_schedules.csv)
    
    Returns:
        List of ScrapingJobConfig objects
    
    Raises:
        FileNotFoundError: If CSV file is not found
        ValueError: If CSV file cannot be read or is invalid
    """
    if csv_path is None:
        # Default CSV path: backend/data/jobs/job_schedules.csv
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        csv_path = os.path.join(backend_dir, "data", "jobs", "job_schedules.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"CSV file not found: {csv_path}\n"
            f"Please create the CSV file with your scraping schedules.\n"
            f"See CSV_SCHEDULER_GUIDE.md for format details."
        )
    
    try:
        schedules = load_schedules_from_csv(csv_path)
        print(f"[INFO] Loaded {len(schedules)} schedules from CSV: {csv_path}")
        return schedules
    except Exception as e:
        raise ValueError(f"Failed to load CSV schedules from {csv_path}: {str(e)}")

