"""
Job data processor for extracting and cleaning job information.
Uses NLP (spaCy) to extract duties and responsibilities.
"""
import re
import pandas as pd
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import spaCy, but make it optional
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Duty extraction will be limited.")


class JobProcessor:
    """Service for processing and enriching job data"""
    
    def __init__(self):
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
    
    def extract_duties_responsibilities(self, description: str) -> List[str]:
        """
        Extract duties and responsibilities from job description.
        
        Args:
            description: Job description text
            
        Returns:
            List of extracted duties/responsibilities
        """
        if pd.isna(description) or not description:
            return []
        
        duties = []
        
        # Heuristic: Look for bullet points or numbered lists
        for line in description.split('\n'):
            line = line.strip()
            # Match bullet points (various formats)
            if re.match(r'^[-*\u2022•\s]*\s*[A-Za-z0-9]', line):
                duties.append(line)
            # Match numbered lists
            elif re.match(r'^\d+\.\s*[A-Za-z0-9]', line):
                duties.append(line)
        
        # If no bullet points found and spaCy is available, use NLP
        if not duties and self.nlp:
            try:
                doc = self.nlp(description)
                duty_keywords = [
                    "responsibilities", "duties", "will be responsible for", "tasks include",
                    "key accountabilities", "you will", "support", "manage", "develop", "implement",
                    "perform", "ensure", "collaborate", "lead", "maintain", "create", "design",
                    "contribute", "prepare", "conduct", "analyze", "report"
                ]
                
                for sent in doc.sents:
                    sentence_text = sent.text.lower()
                    if any(keyword in sentence_text for keyword in duty_keywords):
                        duties.append(sent.text.strip())
            except Exception as e:
                logger.warning(f"Error in NLP processing: {str(e)}")
        
        return duties[:20]  # Limit to 20 duties
    
    def extract_requirements(self, description: str) -> List[str]:
        """
        Extract job requirements from description.
        
        Args:
            description: Job description text
            
        Returns:
            List of requirements
        """
        if pd.isna(description) or not description:
            return []
        
        requirements = []
        
        # Look for requirements section
        req_section_patterns = [
            r'requirements?:?\s*\n(.*?)(?=\n\n|\n[A-Z][a-z]+:|$)',
            r'qualifications?:?\s*\n(.*?)(?=\n\n|\n[A-Z][a-z]+:|$)',
            r'must have:?\s*\n(.*?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        ]
        
        for pattern in req_section_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE | re.DOTALL)
            for match in matches:
                req_text = match.group(1)
                # Extract bullet points from requirements section
                for line in req_text.split('\n'):
                    line = line.strip()
                    if re.match(r'^[-*\u2022•\s]*\s*[A-Za-z0-9]', line) or re.match(r'^\d+\.\s*[A-Za-z0-9]', line):
                        requirements.append(line)
        
        return requirements[:30]  # Limit to 30 requirements
    
    def process_job_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process a DataFrame of jobs and add extracted fields.
        
        Args:
            df: DataFrame with job data (columns: title, company, description, etc.)
            
        Returns:
            DataFrame with additional processed columns
        """
        df = df.copy()
        
        # Extract duties if description column exists
        if 'description' in df.columns:
            df['extracted_duties'] = df['description'].apply(self.extract_duties_responsibilities)
            df['extracted_requirements'] = df['description'].apply(self.extract_requirements)
        
        return df
    
    def prepare_job_for_storage(self, job_row: pd.Series) -> Dict[str, Any]:
        """
        Prepare a single job row for database storage.
        
        Args:
            job_row: Pandas Series with job data
            
        Returns:
            Dictionary with processed job data
        """
        # Helper function to safely extract scalar values from Series
        def safe_get(key, default=None):
            """Safely get a value from Series, handling arrays and NaN"""
            try:
                value = job_row.get(key, default)
                
                # Handle numpy arrays
                try:
                    import numpy as np
                    if isinstance(value, np.ndarray):
                        if value.size > 0:
                            value = value.item() if value.size == 1 else value[0]
                        else:
                            return default
                except ImportError:
                    pass
                
                # Handle pandas Series/Index
                if isinstance(value, (pd.Series, pd.Index)):
                    if len(value) > 0:
                        value = value.iloc[0] if hasattr(value, 'iloc') else value[0]
                    else:
                        return default
                
                # Check if scalar value is not NA
                if pd.isna(value) or (isinstance(value, str) and value == ""):
                    return default
                
                return value
            except Exception as e:
                logger.debug(f"Error extracting {key}: {str(e)}")
                return default
        
        # Extract basic fields
        title = safe_get("title", "")
        company = safe_get("company", "")
        description = safe_get("description", "")
        location = safe_get("location")
        url = safe_get("job_url") or safe_get("url")
        source = safe_get("site") or safe_get("source")
        
        job_data = {
            "title": str(title) if title else "",
            "company": str(company) if company else "",
            "description": str(description) if description else "",
            "location": str(location) if location else None,
            "url": str(url) if url else None,
            "source": str(source) if source else None,
        }
        
        # Extract salary if available
        salary = safe_get("salary")
        if salary:
            # Try to parse salary range
            salary_str = str(salary)
            # Simple parsing (can be enhanced)
            if "-" in salary_str:
                parts = salary_str.split("-")
                if len(parts) == 2:
                    try:
                        job_data["salary_min"] = int(re.sub(r'[^\d]', '', parts[0]))
                        job_data["salary_max"] = int(re.sub(r'[^\d]', '', parts[1]))
                    except ValueError:
                        pass
        
        # Extract posted date
        date_posted = safe_get("date_posted") or safe_get("posted_date")
        if date_posted:
            try:
                if isinstance(date_posted, str):
                    # Try to parse date string
                    from datetime import datetime
                    job_data["posted_date"] = datetime.strptime(date_posted, "%Y-%m-%d").date()
                else:
                    job_data["posted_date"] = date_posted
            except Exception:
                pass
        
        # Extract requirements
        requirements = []
        extracted_reqs = safe_get("extracted_requirements")
        if extracted_reqs:
            # If it's already a list, use it; otherwise convert
            if isinstance(extracted_reqs, list):
                requirements = extracted_reqs
            else:
                requirements = [str(extracted_reqs)]
        else:
            req = safe_get("requirements")
            if req:
                if isinstance(req, list):
                    requirements = req
                else:
                    requirements = [str(req)]
        
        job_data["requirements"] = requirements if requirements else []
        
        return job_data

