"""
Main job scraper service that orchestrates scraping, processing, and storage.
Coordinates all components to scrape jobs and save them to PostgreSQL and Qdrant.
"""
import asyncio
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import csv

from .scraper import JobScraper
from .processor import JobProcessor
from .database_service import DatabaseService
from .qdrant_service import QdrantService
from .embedding_service import EmbeddingService
from .config import get_scraper_settings

logger = logging.getLogger(__name__)


class JobScraperService:
    """
    Main service for scraping jobs and saving to PostgreSQL and Qdrant.
    """
    
    def __init__(self):
        self.settings = get_scraper_settings()
        self.scraper = JobScraper()
        self.processor = JobProcessor()
        self.database = DatabaseService()
        self.qdrant = QdrantService()
        self.embedding_service = EmbeddingService()
        
        # Ensure Qdrant collection exists
        self.qdrant.ensure_collection()
    
    async def scrape_and_save(
        self,
        search_term: str,
        location: str = "Hong Kong",
        google_search_term: Optional[str] = None,
        results_wanted: Optional[int] = None,
        hours_old: Optional[int] = None,
        sites: Optional[List[str]] = None,
        country_indeed: Optional[str] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scrape jobs and save them to PostgreSQL and Qdrant.
        
        Args:
            search_term: Job search term
            location: Job location
            google_search_term: Custom Google search term
            results_wanted: Number of results to fetch
            hours_old: Maximum age of jobs in hours
            sites: List of sites to scrape
            country_indeed: Country for Indeed search
            batch_size: Batch size for processing (default: from config)
            
        Returns:
            Dictionary with scraping results:
            {
                "scraped": int,      # Number of jobs scraped
                "saved": int,        # Number of jobs saved to database
                "failed": int,        # Number of jobs that failed to save
                "skipped": int,       # Number of duplicate jobs skipped
                "qdrant_saved": int,  # Number of jobs saved to Qdrant
                "qdrant_failed": int  # Number of jobs that failed to save to Qdrant
            }
        """
        batch_size = batch_size or self.settings.batch_size
        
        logger.info("=" * 60)
        logger.info("Starting Job Scraping Process")
        logger.info("=" * 60)
        
        # Step 1: Scrape jobs
        logger.info(f"Step 1: Scraping jobs for '{search_term}' in '{location}'...")
        try:
            jobs_df = self.scraper.scrape(
                search_term=search_term,
                location=location,
                google_search_term=google_search_term,
                results_wanted=results_wanted,
                hours_old=hours_old,
                sites=sites,
                country_indeed=country_indeed
            )
            logger.info(f"✅ Scraped {len(jobs_df)} jobs")
        except Exception as e:
            logger.error(f"❌ Error scraping jobs: {str(e)}")
            return {
                "scraped": 0,
                "saved": 0,
                "failed": 0,
                "skipped": 0,
                "qdrant_saved": 0,
                "qdrant_failed": 0,
                "error": str(e)
            }
        
        if len(jobs_df) == 0:
            logger.warning("No jobs found")
            return {
                "scraped": 0,
                "saved": 0,
                "failed": 0,
                "skipped": 0,
                "qdrant_saved": 0,
                "qdrant_failed": 0
            }
        
        # Step 2: Process jobs
        logger.info("Step 2: Processing jobs...")
        processed_df = self.processor.process_job_dataframe(jobs_df)
        logger.info(f"✅ Processed {len(processed_df)} jobs")
        
        # Step 3: Save jobs to database and Qdrant
        logger.info("Step 3: Saving jobs to database and Qdrant...")
        results = await self._save_jobs_batch(processed_df, batch_size, jobs_df)
        
        # Step 4: Save CSV file
        logger.info("Step 4: Saving CSV file...")
        csv_path = self._save_csv_file(jobs_df, results)
        if csv_path:
            logger.info(f"✅ CSV file saved: {csv_path}")
            results['csv_file'] = csv_path
        
        logger.info("=" * 60)
        logger.info("Scraping Process Complete")
        logger.info("=" * 60)
        logger.info(f"Scraped: {results['scraped']}")
        logger.info(f"Saved to PostgreSQL: {results['saved']}")
        logger.info(f"Failed: {results['failed']}")
        logger.info(f"Skipped (duplicates): {results['skipped']}")
        logger.info(f"Saved to Qdrant: {results['qdrant_saved']}")
        logger.info(f"Qdrant failed: {results['qdrant_failed']}")
        
        return results
    
    async def _save_jobs_batch(
        self,
        jobs_df: pd.DataFrame,
        batch_size: int,
        original_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Save jobs in batches to PostgreSQL and Qdrant.
        Tracks which jobs were saved for CSV export.
        """
        stats = {
            "scraped": len(jobs_df),
            "saved": 0,
            "failed": 0,
            "skipped": 0,
            "qdrant_saved": 0,
            "qdrant_failed": 0,
            "saved_job_ids": []  # Track which jobs were successfully saved
        }
        
        total = len(jobs_df)
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = jobs_df.iloc[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} jobs)...")
            
            # Prepare batch data
            job_texts = []
            job_data_list = []
            
            for idx, row in batch.iterrows():
                try:
                    job_data = self.processor.prepare_job_for_storage(row)
                    job_data_list.append(job_data)
                    
                    # Prepare text for embedding (combine title, description, requirements)
                    text_parts = []
                    if job_data.get("title"):
                        text_parts.append(f"Job Title: {job_data['title']}")
                    if job_data.get("description"):
                        text_parts.append(f"Description: {job_data['description']}")
                    if job_data.get("requirements"):
                        req_text = " ".join(job_data["requirements"][:5])  # Limit requirements
                        text_parts.append(f"Requirements: {req_text}")
                    
                    job_texts.append("\n".join(text_parts))
                except Exception as e:
                    logger.warning(f"Error preparing job {idx}: {str(e)}")
                    stats["failed"] += 1
                    continue
            
            # Generate embeddings for batch
            logger.info(f"  Generating embeddings for batch {batch_num}...")
            try:
                embeddings = await self.embedding_service.generate_embeddings_batch(job_texts)
            except Exception as e:
                logger.error(f"  Error generating embeddings: {str(e)}")
                # Use zero vectors as fallback
                dim = self.settings.embedding_dim
                embeddings = [[0.0] * dim] * len(job_texts)
            
            # Save each job
            for job_data, embedding, job_text in zip(job_data_list, embeddings, job_texts):
                try:
                    # Check for duplicates using vector search if enabled
                    existing_job_id = None
                    if self.settings.enable_duplicate_detection:
                        # First try URL-based check (fast)
                        if job_data.get("url"):
                            existing_job_id = self.database.job_exists(
                                url=job_data.get("url"),
                                title=job_data["title"],
                                company=job_data["company"]
                            )
                        
                        # If not found and vector detection is enabled, try vector search
                        if not existing_job_id and self.settings.use_vector_duplicate_detection:
                            existing_job_id = self.qdrant.find_duplicate_job(
                                vector=embedding,
                                title=job_data["title"],
                                company=job_data["company"],
                                location=job_data.get("location"),
                                similarity_threshold=self.settings.duplicate_similarity_threshold
                            )
                        
                        if existing_job_id:
                            logger.info(
                                f"Duplicate job detected: {job_data['title']} at {job_data['company']} "
                                f"(existing ID: {existing_job_id})"
                            )
                            stats["skipped"] += 1
                            continue
                    
                    # Save to PostgreSQL
                    job_id = self.database.save_job(
                        title=job_data["title"],
                        company=job_data["company"],
                        description=job_data["description"],
                        requirements=job_data["requirements"],
                        location=job_data.get("location"),
                        salary_min=job_data.get("salary_min"),
                        salary_max=job_data.get("salary_max"),
                        url=job_data.get("url"),
                        source=job_data.get("source"),
                        posted_date=job_data.get("posted_date"),
                        embedding=embedding
                    )
                    
                    if job_id:
                        stats["saved"] += 1
                        stats["saved_job_ids"].append(job_id)
                        
                        # Prepare payload for Qdrant
                        qdrant_payload = {
                            "job_id": job_id,
                            "title": job_data["title"],
                            "company": job_data["company"],
                            "location": job_data.get("location", ""),
                            "description": job_data["description"],
                            "requirements": job_data["requirements"],
                            "url": job_data.get("url", ""),
                            "source": job_data.get("source", ""),
                            "salary_min": job_data.get("salary_min"),
                            "salary_max": job_data.get("salary_max"),
                        }
                        
                        # Save to Qdrant
                        if self.qdrant.save_job_data(
                            job_id=job_id,
                            vector=embedding,
                            payload=qdrant_payload
                        ):
                            stats["qdrant_saved"] += 1
                        else:
                            stats["qdrant_failed"] += 1
                    else:
                        # Job save failed (not a duplicate, since duplicates are caught earlier)
                        stats["failed"] += 1
                        logger.warning(f"Failed to save job: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
                            
                except Exception as e:
                    logger.error(f"  Error saving job '{job_data.get('title', 'Unknown')}': {str(e)}")
                    stats["failed"] += 1
            
            # Progress update
            progress = ((i + len(batch)) / total) * 100
            logger.info(f"  ✅ Progress: {i + len(batch)}/{total} ({progress:.1f}%)")
        
        return stats
    
    def _save_csv_file(
        self,
        jobs_df: pd.DataFrame,
        results: Dict[str, Any]
    ) -> Optional[str]:
        """
        Save scraped jobs to CSV file with timestamp and save status.
        
        Args:
            jobs_df: DataFrame with scraped jobs
            results: Results dictionary with save status
            
        Returns:
            Path to saved CSV file, or None if failed
        """
        try:
            # Create data/jobs directory if it doesn't exist
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            jobs_dir = os.path.join(backend_dir, "data", "jobs")
            os.makedirs(jobs_dir, exist_ok=True)
            
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Determine save status for filename
            saved_count = results.get("saved", 0)
            total_count = results.get("scraped", len(jobs_df))
            if saved_count > 0:
                save_status = f"saved_{saved_count}of{total_count}"
            else:
                save_status = "not_saved"
            
            # Create filename with timestamp and save status
            filename = f"jobs_{timestamp}_{save_status}.csv"
            filepath = os.path.join(jobs_dir, filename)
            
            # Add save status column to DataFrame
            df_to_save = jobs_df.copy()
            
            # Try to match jobs with saved status (using URL as identifier)
            # Since we don't have direct mapping, we'll add a general status
            df_to_save['saved_to_database'] = 'Unknown'
            df_to_save['scrape_timestamp'] = timestamp
            df_to_save['total_scraped'] = total_count
            df_to_save['total_saved'] = saved_count
            df_to_save['total_failed'] = results.get("failed", 0)
            df_to_save['total_skipped'] = results.get("skipped", 0)
            
            # Save to CSV
            df_to_save.to_csv(
                filepath,
                index=False,
                quoting=csv.QUOTE_NONNUMERIC,
                escapechar="\\",
                encoding='utf-8-sig'  # UTF-8 with BOM for Excel compatibility
            )
            
            logger.info(f"CSV file saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving CSV file: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get Qdrant collection information"""
        return self.qdrant.get_collection_info()


# Convenience function for async usage
async def scrape_and_save_jobs(
    search_term: str,
    location: str = "Hong Kong",
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to scrape and save jobs.
    
    Usage:
        result = await scrape_and_save_jobs("Software Engineer", "Hong Kong")
    """
    service = JobScraperService()
    return await service.scrape_and_save(search_term, location, **kwargs)

