"""
Job Scraping Service

A comprehensive service for scraping jobs from multiple sources,
processing them, and storing in PostgreSQL (direct connection) and Qdrant.
"""

from .job_scraper_service import JobScraperService

__all__ = ["JobScraperService"]

