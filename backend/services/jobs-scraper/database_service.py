"""
Database service for PostgreSQL operations.
Handles job storage and retrieval using direct PostgreSQL connection.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from contextlib import contextmanager
from .config import get_scraper_settings
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for PostgreSQL database operations"""
    
    def __init__(self):
        self.settings = get_scraper_settings()
        self._connection = None
    
    def _get_connection(self):
        """Get or create PostgreSQL connection"""
        if self._connection is None or self._connection.closed:
            try:
                if self.settings.postgres_connection_string:
                    # Use connection string if provided
                    self._connection = psycopg2.connect(
                        self.settings.postgres_connection_string
                    )
                else:
                    # Use individual parameters
                    self._connection = psycopg2.connect(
                        host=self.settings.postgres_host,
                        port=self.settings.postgres_port,
                        database=self.settings.postgres_database,
                        user=self.settings.postgres_user,
                        password=self.settings.postgres_password
                    )
                logger.debug("PostgreSQL connection established")
            except Exception as e:
                logger.error(f"Error connecting to PostgreSQL: {str(e)}")
                raise
        return self._connection
    
    @contextmanager
    def _get_cursor(self):
        """Get a database cursor with context management"""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def job_exists(self, url: str, title: str, company: str) -> Optional[str]:
        """
        Check if a job already exists in the database.
        Returns the job ID if found, None otherwise.
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id FROM jobs 
                    WHERE url = %s AND title = %s AND company = %s 
                    LIMIT 1
                    """,
                    (url, title, company)
                )
                result = cursor.fetchone()
                if result:
                    return str(result['id'])
                return None
        except Exception as e:
            logger.warning(f"Error checking for existing job: {str(e)}")
            return None
    
    def save_job(
        self,
        title: str,
        company: str,
        description: str,
        requirements: List[str],
        location: Optional[str] = None,
        salary: Optional[str] = None,
        url: Optional[str] = None,
        source: Optional[str] = None,
        posted_date: Optional[date] = None,
        embedding: Optional[List[float]] = None,
        is_active: bool = True
    ) -> Optional[str]:
        """
        Save a job to the database.
        Returns the job ID if successful, None otherwise.
        """
        try:
            # Note: Duplicate detection is now handled in job_scraper_service using vector search
            # This method is called after duplicate check, so we proceed with saving
            
            with self._get_cursor() as cursor:
                # Check which columns exist in the table
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'jobs'
                """)
                existing_columns = {row['column_name'] for row in cursor.fetchall()}
                
                # Build dynamic INSERT query based on available columns
                base_columns = ['title', 'company', 'description', 'requirements', 'location', 
                               'url', 'source', 'posted_date', 'is_active', 'retrieved_date']
                optional_columns = []
                values = []
                
                # Add base columns
                for col in base_columns:
                    if col in existing_columns:
                        optional_columns.append(col)
                        if col == 'requirements':
                            values.append(requirements)
                        elif col == 'posted_date':
                            values.append(posted_date)
                        elif col == 'is_active':
                            values.append(is_active)
                        elif col == 'retrieved_date':
                            values.append(datetime.utcnow())
                        elif col == 'title':
                            values.append(title)
                        elif col == 'company':
                            values.append(company)
                        elif col == 'description':
                            values.append(description)
                        elif col == 'location':
                            values.append(location)
                        elif col == 'url':
                            values.append(url)
                        elif col == 'source':
                            values.append(source)
                
                # Add salary column if it exists
                if 'salary' in existing_columns and salary is not None:
                    optional_columns.append('salary')
                    values.append(salary)
                
                # Add embedding if column exists and embedding is provided
                embedding_value = None
                if 'embedding' in existing_columns and embedding:
                    # Check if embedding dimension matches PostgreSQL schema (768)
                    if len(embedding) == 768:
                        optional_columns.append('embedding')
                        embedding_value = embedding
                        values.append(embedding_value)
                    else:
                        logger.debug(f"Skipping PostgreSQL embedding (dim={len(embedding)}, expected 768)")
                
                # Build and execute INSERT query
                columns_str = ', '.join(optional_columns)
                placeholders = ', '.join(['%s'] * len(values))
                insert_query = f"""
                    INSERT INTO jobs ({columns_str})
                    VALUES ({placeholders})
                    RETURNING id
                """
                
                cursor.execute(insert_query, tuple(values))
                
                result = cursor.fetchone()
                if result:
                    job_id = str(result['id'])
                    logger.info(f"Saved job: {title} at {company} (ID: {job_id})")
                    return job_id
                else:
                    logger.error(f"Failed to save job: {title} at {company}")
                    return None
                
        except Exception as e:
            logger.error(f"Error saving job to database: {str(e)}")
            return None
    
    def update_job_embedding(self, job_id: str, embedding: List[float]) -> bool:
        """
        Update the embedding for an existing job.
        """
        try:
            # Only update if dimension matches
            if len(embedding) != 768:
                logger.warning(f"Cannot update embedding: dimension mismatch (got {len(embedding)}, expected 768)")
                return False
            
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE jobs 
                    SET embedding = %s 
                    WHERE id = %s
                    """,
                    (embedding, job_id)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating job embedding: {str(e)}")
            return False
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by its ID"""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM jobs WHERE id = %s LIMIT 1",
                    (job_id,)
                )
                result = cursor.fetchone()
                if result:
                    # Convert to regular dict
                    return dict(result)
                return None
        except Exception as e:
            logger.error(f"Error getting job by ID: {str(e)}")
            return None
    
    def close(self):
        """Close the database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.debug("PostgreSQL connection closed")
