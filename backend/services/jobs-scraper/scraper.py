"""
Job scraper using jobspy library.
Scrapes jobs from multiple sources (Indeed, LinkedIn, Google).
"""
import pandas as pd
from typing import List, Optional, Dict, Any
from jobspy import scrape_jobs
from .config import get_scraper_settings
import logging

logger = logging.getLogger(__name__)


class JobScraper:
    """Service for scraping jobs from multiple sources"""
    
    def __init__(self):
        self.settings = get_scraper_settings()
    
    def scrape(
        self,
        search_term: str,
        location: str = "Hong Kong",
        google_search_term: Optional[str] = None,
        results_wanted: Optional[int] = None,
        hours_old: Optional[int] = None,
        sites: Optional[List[str]] = None,
        country_indeed: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Scrape jobs from multiple sources.
        
        Args:
            search_term: Job search term (e.g., "Software Engineer")
            location: Job location (default: "Hong Kong")
            google_search_term: Custom Google search term (optional)
            results_wanted: Number of results to fetch (default: from config)
            hours_old: Maximum age of jobs in hours (default: from config)
            sites: List of sites to scrape (default: from config)
            country_indeed: Country for Indeed search (default: location)
            
        Returns:
            DataFrame with scraped jobs
        """
        # Use settings defaults if not provided
        results_wanted = results_wanted or self.settings.scrape_results_wanted
        hours_old = hours_old or self.settings.scrape_hours_old
        sites = sites or self.settings.scrape_sites
        country_indeed = country_indeed or location
        google_search_term = google_search_term or f"{search_term} jobs in {location}"
        
        logger.info(f"Scraping jobs: search_term='{search_term}', location='{location}', sites={sites}")
        
        try:
            jobs = scrape_jobs(
                site_name=sites,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed=country_indeed,
                linkedin_fetch_description=True,
                google_search_term=google_search_term
            )
            
            logger.info(f"Scraped {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping jobs: {str(e)}")
            raise

