"""
Application tracking API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Body
from fastapi.responses import StreamingResponse
from typing import List, Optional
import os
import json
import time
from urllib.parse import quote

from models.application import (
    ApplicationCreate, Application, ApplicationWithJob, ApplicationStatus,
    ApplicationUpdate, ApplicationStatusEnum
)
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient
import sys

# Import LLM service from jobs-finder directory
services_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'jobs-finder')
sys.path.insert(0, services_path)
from llm_service import llm_service

# Import tailored CV service
# TailoredCVService replaced by AgenticCVService
# from services.cv.tailored_cv_service import get_tailored_cv_service

router = APIRouter()

# Valid statuses
VALID_STATUSES = [s.value for s in ApplicationStatusEnum]


def encode_filename_for_header(filename: str) -> str:
    """
    Encode filename for HTTP Content-Disposition header to handle non-ASCII characters.
    Uses RFC 2231 encoding format: filename*=UTF-8''encoded_filename
    Also provides a fallback ASCII filename for compatibility.
    
    Returns a header value that is guaranteed to be encodable as latin-1.
    """
    try:
        # Check if filename contains non-ASCII characters
        filename.encode('ascii')
        # If no error, filename is ASCII-safe, use simple format
        return f'attachment; filename="{filename}"'
    except UnicodeEncodeError:
        # Filename contains non-ASCII characters, use RFC 2231 encoding
        # URL-encode the filename for the UTF-8 version (RFC 2231)
        encoded_filename = quote(filename, safe='')
        # Provide both ASCII fallback and UTF-8 encoded version
        # ASCII fallback: remove non-ASCII characters, ensure it's not empty
        ascii_fallback = filename.encode('ascii', 'ignore').decode('ascii').strip()
        if not ascii_fallback or ascii_fallback == '.pdf':
            ascii_fallback = 'CV.pdf'
        # RFC 2231 format: filename*=UTF-8''encoded_filename
        # All characters in this string are ASCII, so it's latin-1 encodable
        return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_filename}'


@router.post("/mark-applied", response_model=Application, status_code=status.HTTP_201_CREATED)
async def mark_job_applied(
    application: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Mark a job with a status (create or update application).
    This endpoint supports all statuses: saved, applied, interviewing, offer, accepted, rejected, declined, withdrawn, not_interested
    """
    # Validate status
    app_status = application.status or "saved"
    if app_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
        )
    
    job_exists = await db.fetch_one("SELECT id FROM jobs WHERE id = $1", application.job_id)
    if not job_exists:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if application already exists
    existing = await db.fetch_one(
        "SELECT id, status FROM applications WHERE user_id = $1 AND job_id = $2",
        current_user["id"], application.job_id
    )
    
    if existing:
        # Update existing application
        app_id = existing["id"]
        await db.execute(
            """UPDATE applications 
               SET status = $1, notes = $2, updated_at = NOW(),
                   submitted_at = CASE WHEN $1 = 'applied' AND submitted_at IS NULL THEN NOW() ELSE submitted_at END
               WHERE id = $3""",
            app_status, application.notes, app_id
        )
    else:
        # Create new application
        app_id = await db.fetch_val(
            """INSERT INTO applications (user_id, job_id, status, notes, submitted_at)
               VALUES ($1, $2, $3, $4, CASE WHEN $3 = 'applied' THEN NOW() ELSE NULL END)
               RETURNING id""",
            current_user["id"], application.job_id, app_status, application.notes
        )
    
    result = await db.fetch_one(
        "SELECT * FROM applications WHERE id = $1", app_id
    )
    
    return {
        "id": str(result["id"]),
        "user_id": str(result["user_id"]),
        "job_id": str(result["job_id"]),
        "status": result["status"],
        "notes": result["notes"],
        "submitted_at": result["submitted_at"],
        "created_at": result["created_at"],
        "updated_at": result["updated_at"]
    }


@router.put("/{job_id}/status", response_model=Application)
async def update_application_status(
    job_id: str,
    update: ApplicationUpdate,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Update application status for a job.
    """
    # Validate status
    if update.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
        )
    
    # Check if application exists
    existing = await db.fetch_one(
        "SELECT id FROM applications WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update status
    await db.execute(
        """UPDATE applications 
           SET status = $1, notes = $2, updated_at = NOW(),
               submitted_at = CASE WHEN $1 = 'applied' AND submitted_at IS NULL THEN NOW() ELSE submitted_at END
           WHERE id = $3""",
        update.status, update.notes, existing["id"]
    )
    
    result = await db.fetch_one(
        "SELECT * FROM applications WHERE id = $1", existing["id"]
    )
    
    return {
        "id": str(result["id"]),
        "user_id": str(result["user_id"]),
        "job_id": str(result["job_id"]),
        "status": result["status"],
        "notes": result["notes"],
        "submitted_at": result["submitted_at"],
        "created_at": result["created_at"],
        "updated_at": result["updated_at"]
    }


@router.get("/", response_model=dict)
async def get_applications(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get all applications for current user with job details.
    """
    applications = await db.fetch_all(
        """SELECT a.id, a.job_id, a.status, a.notes, a.submitted_at, a.created_at, a.updated_at,
                  j.id as j_id, j.title, j.company, j.location, j.salary,
                  j.description, j.url, j.posted_date
           FROM applications a
           LEFT JOIN jobs j ON a.job_id = j.id
           WHERE a.user_id = $1
           ORDER BY a.updated_at DESC, a.created_at DESC""",
        current_user["id"]
    )
    
    return {
        "applications": [{
            "id": str(app["id"]),
            "job_id": str(app["job_id"]),
            "status": app["status"],
            "notes": app["notes"],
            "applied_at": app["submitted_at"] or app["created_at"],
            "created_at": app["created_at"],
            "updated_at": app["updated_at"],
            "job": {
                "id": str(app["j_id"]) if app["j_id"] else str(app["job_id"]),
                "title": app["title"] or "Unknown",
                "company": app["company"] or "Unknown",
                "location": app["location"],
                "description": app["description"],
                "job_url": app["url"],
                "posted_date": app["posted_date"]
            }
        } for app in applications]
    }


@router.get("/status/{job_id}", response_model=dict)
async def check_application_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Check application status for a specific job.
    Returns the full application record if it exists.
    """
    application = await db.fetch_one(
        "SELECT id, status, notes, submitted_at FROM applications WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )
    
    if application:
        return {
            "job_id": job_id,
            "has_application": True,
            "application_id": str(application["id"]),
            "status": application["status"],
            "notes": application["notes"],
            "submitted_at": application["submitted_at"]
        }
    
    return {
        "job_id": job_id,
        "has_application": False,
        "application_id": None,
        "status": None,
        "notes": None,
        "submitted_at": None
    }


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_application(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Remove application record (unmark as applied).
    """
    result = await db.execute(
        "DELETE FROM applications WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )
    
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Application not found")
    
    return None


def detect_domain_from_job(job_title: str, job_description: str) -> str:
    """Detect if job is IT or Finance based on title and description."""
    text = f"{job_title} {job_description}".lower()
    
    # IT keywords
    it_keywords = [
        'software', 'developer', 'engineer', 'programmer', 'coding', 'python', 'java', 'javascript',
        'react', 'node', 'api', 'database', 'sql', 'devops', 'cloud', 'aws', 'azure', 'kubernetes',
        'docker', 'backend', 'frontend', 'full stack', 'machine learning', 'ai', 'data science',
        'cybersecurity', 'network', 'system', 'technical', 'it', 'information technology'
    ]
    
    # Finance keywords
    finance_keywords = [
        'finance', 'financial', 'accounting', 'accountant', 'audit', 'tax', 'investment', 'banking',
        'bank', 'trading', 'portfolio', 'risk', 'compliance', 'analyst', 'cfo', 'controller',
        'bookkeeping', 'budget', 'forecast', 'revenue', 'profit', 'loss', 'balance sheet',
        'financial planning', 'wealth management', 'asset management'
    ]
    
    it_score = sum(1 for keyword in it_keywords if keyword in text)
    finance_score = sum(1 for keyword in finance_keywords if keyword in text)
    
    if it_score > finance_score and it_score > 0:
        return "IT"
    elif finance_score > it_score and finance_score > 0:
        return "Finance"
    else:
        return "General"


@router.post("/{job_id}/prepare/interview", response_model=dict)
async def prepare_interview_for_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Start interview prep session for a specific job.
    Automatically detects domain (IT/Finance) from job description.
    """
    # Get job details
    job = await db.fetch_one(
        "SELECT id, title, company, description FROM jobs WHERE id = $1",
        job_id
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user has saved/applied to this job
    application = await db.fetch_one(
        "SELECT id, status FROM applications WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )
    
    if not application:
        raise HTTPException(
            status_code=400,
            detail="You must save or apply to this job before preparing for interview"
        )
    
    # Detect domain from job
    domain = detect_domain_from_job(job.get("title", ""), job.get("description", ""))
    role_type = domain if domain != "General" else "IT"  # Default to IT if unclear
    
    # Create interview session using PostgreSQL
    from datetime import datetime
    import uuid
    
    session_id = str(uuid.uuid4())
    user_id = current_user["id"]
    started_at = datetime.utcnow()
    
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    try:
        session_id_db = await db.fetch_val(
            """INSERT INTO interview_sessions 
               (id, user_id, role_type, domain, job_id, status, total_questions, completed_questions, started_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
               RETURNING id""",
            session_id, user_id, role_type, domain, job_id, "active", 5, 0, started_at
        )
        session_id = str(session_id_db) if session_id_db else session_id
        
        return {
            "session_id": session_id,
            "job_id": job_id,
            "job_title": job.get("title"),
            "company": job.get("company"),
            "domain": domain,
            "redirect_url": f"/interview/session/{session_id}"
        }
    except Exception as e:
        print(f"Error creating interview session: {e}")
        import traceback
        traceback.print_exc()
        # Check if it's a table not found error
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "relation" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Interview tables not found. Please run the interview migration: python backend/scripts/run_interview_migration.py"
            )
        raise HTTPException(status_code=500, detail=f"Failed to start interview session: {str(e)}")


@router.post("/{job_id}/prepare/cv", response_model=dict)
async def generate_tailored_cv(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Generate a tailored HTML CV for a specific job.
    Generates a professional HTML CV customized for the job description.
    
    Returns:
        - tailored_cv_id: ID of the generated/updated CV
        - job_id: Job ID
        - job_title: Job title
        - company: Company name
        - html_content: Generated HTML content (if successful)
        - emphasis_notes: Notes about what was emphasized
        - redirect_url: URL to view the CV
        - success: Whether generation was successful
        - error: Error message if failed
    """
    # Validate job exists
    job = await db.fetch_one(
        "SELECT id, title, company, description FROM jobs WHERE id = $1",
        job_id
    )
    
    if not job:
        raise HTTPException(
            status_code=404, 
            detail="Job not found. Please select a valid job."
        )
    
    # Validate job has description
    job_description = job.get('description', '').strip()
    if not job_description:
        raise HTTPException(
            status_code=400,
            detail="Job description is missing. Cannot generate tailored CV without job details."
        )
    
    # Get user's CV profile with better error messages
    cv_profile = await db.fetch_one(
        "SELECT id, raw_text, parsed_data, updated_at FROM cv_profiles WHERE user_id = $1",
        current_user["id"]
    )
    
    if not cv_profile:
        raise HTTPException(
            status_code=400,
            detail="CV profile not found. Please upload your CV in the Profile page first."
        )
    
    # Parse CV data with better validation
    parsed_data = cv_profile.get("parsed_data")
    if isinstance(parsed_data, str):
        try:
            parsed_data = json.loads(parsed_data)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"CV data is corrupted. Please re-upload your CV. Error: {str(e)}"
            )
    
    if not parsed_data:
        raise HTTPException(
            status_code=400,
            detail="CV data is empty or not properly parsed. Please re-upload your CV."
        )
    
    # Validate CV has essential data
    has_work_experience = bool(parsed_data.get("work_experience"))
    has_education = bool(parsed_data.get("education"))
    has_skills = bool(parsed_data.get("skills"))
    
    if not (has_work_experience or has_education or has_skills):
        raise HTTPException(
            status_code=400,
            detail="CV data is incomplete. Please ensure your CV contains work experience, education, or skills."
        )
    
    # Generate tailored HTML CV using the agentic service
    try:
        # Always use agentic CV service (replaces tailored_cv_service)
        try:
            from backend.services.cv.agentic_cv_service import get_agentic_cv_service
        except ImportError:
            from services.cv.agentic_cv_service import get_agentic_cv_service
        cv_service = get_agentic_cv_service()
        print("🤖 Using agentic CV generation (multi-step reasoning)")
        
        # Generate CV with retry logic built into the service
        result = await cv_service.generate_tailored_cv_html(
            cv_parsed_data=parsed_data,
            job_description=job_description,
            job_title=job.get('title', ''),
            company=job.get('company', ''),
            max_attempts=3  # Service handles retries
        )
        
        if not result["success"]:
            error_msg = result.get("error", "Failed to generate tailored CV")
            # Provide more helpful error messages
            if "LLM" in error_msg or "timeout" in error_msg.lower():
                error_msg = f"CV generation service is temporarily unavailable. {error_msg} Please try again in a moment."
            elif "empty" in error_msg.lower() or "invalid" in error_msg.lower():
                error_msg = f"CV data issue: {error_msg} Please check your CV profile."
            
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # Safely extract result fields with defaults
        html_content = result.get("html_content")
        emphasis_notes = result.get("emphasis_notes", "")
        
        # Validate HTML content was generated
        if not html_content or not html_content.strip():
            raise HTTPException(
                status_code=500,
                detail="CV generation completed but no HTML content was produced. Please try again."
            )
        
        # Store both HTML and structured data for backward compatibility
        tailored_data = {
            "html_content": html_content,
            "format": "html",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "job_title": job.get('title'),
            "company": job.get('company'),
            "version": "1.0"  # For future versioning
        }
        
        # Check if tailored CV already exists for this job
        existing_cv = await db.fetch_one(
            "SELECT id, created_at FROM tailored_cvs WHERE user_id = $1 AND job_id = $2",
            current_user["id"], job_id
        )
        
        if existing_cv:
            # Update existing tailored CV
            await db.execute(
                """UPDATE tailored_cvs 
                   SET tailored_content = $1, emphasis_notes = $2, updated_at = NOW()
                   WHERE id = $3""",
                json.dumps(tailored_data),
                emphasis_notes,
                existing_cv["id"]
            )
            tailored_cv_id = existing_cv["id"]
            is_new = False
        else:
            # Create new tailored CV
            tailored_cv_id = await db.fetch_val(
                """INSERT INTO tailored_cvs (user_id, job_id, original_cv_profile_id, tailored_content, emphasis_notes, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                   RETURNING id""",
                current_user["id"],
                job_id,
                cv_profile["id"],
                json.dumps(tailored_data),
                emphasis_notes
            )
            is_new = True
        
        # Include agent steps if available (for agentic CV generation)
        agent_steps = result.get("agent_steps", [])
        refinement_rounds = result.get("refinement_rounds", 0)
        final_quality_score = result.get("final_quality_score", 0)
        
        return {
            "tailored_cv_id": str(tailored_cv_id),
            "job_id": job_id,
            "job_title": job.get("title"),
            "company": job.get("company"),
            "html_content": html_content,
            "emphasis_notes": emphasis_notes,
            "original_cv_id": str(cv_profile["id"]),
            "redirect_url": f"/applications/prepare/cv/{tailored_cv_id}",
            "success": True,
            "is_new": is_new,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent_steps": agent_steps,
            "refinement_rounds": refinement_rounds,
            "final_quality_score": final_quality_score
        }
    
    except HTTPException:
        raise
    except KeyError as e:
        # Handle missing keys in result dictionary
        print(f"KeyError in CV generation result: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"CV generation service returned incomplete data. Missing key: {str(e)}. Please try again."
        )
    except Exception as e:
        print(f"Error generating tailored CV: {e}")
        import traceback
        traceback.print_exc()
        
        # Provide more specific error messages
        error_detail = str(e)
        error_type = type(e).__name__
        
        if "timeout" in error_detail.lower():
            error_detail = "CV generation timed out. The service may be busy. Please try again."
        elif "connection" in error_detail.lower() or "network" in error_detail.lower():
            error_detail = "Network error during CV generation. Please check your connection and try again."
        elif "KeyError" in error_type:
            error_detail = f"Missing required data in CV generation response: {error_detail}"
        elif "AttributeError" in error_type:
            error_detail = f"Service configuration error: {error_detail}. Please check service setup."
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate tailored CV: {error_detail}"
        )


@router.post("/{job_id}/prepare/cover-letter", response_model=dict)
async def generate_cover_letter(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Generate a personalized cover letter for a specific job.
    """
    # Get job details
    job = await db.fetch_one(
        "SELECT id, title, company, description, location FROM jobs WHERE id = $1",
        job_id
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get user's CV profile
    cv_profile = await db.fetch_one(
        "SELECT id, raw_text, parsed_data FROM cv_profiles WHERE user_id = $1",
        current_user["id"]
    )
    
    if not cv_profile:
        raise HTTPException(
            status_code=400,
            detail="Please upload your CV first in the Profile page"
        )
    
    # Parse CV data
    parsed_data = cv_profile.get("parsed_data")
    if isinstance(parsed_data, str):
        try:
            parsed_data = json.loads(parsed_data)
        except:
            parsed_data = {}
    
    # Extract key info from CV
    personal_info = parsed_data.get("personal_info", {}) if isinstance(parsed_data, dict) else {}
    work_experience = parsed_data.get("work_experience", []) if isinstance(parsed_data, dict) else []
    skills = parsed_data.get("skills", {}) if isinstance(parsed_data, dict) else {}
    
    # Use LLM to generate cover letter
    try:
        prompt = f"""Write a professional, personalized cover letter for this job application.

Job Details:
- Title: {job.get('title', '')}
- Company: {job.get('company', '')}
- Location: {job.get('location', '')}
- Description: {job.get('description', '')[:1500]}

Applicant Information:
- Name: {personal_info.get('first_name', '')} {personal_info.get('last_name', '')}
- Email: {personal_info.get('email', '')}
- Recent Experience: {json.dumps(work_experience[:2], indent=2) if work_experience else 'Not provided'}
- Key Skills: {json.dumps(skills, indent=2) if skills else 'Not provided'}

Instructions:
1. Write a compelling cover letter (3-4 paragraphs)
2. Address it to the hiring manager
3. Show enthusiasm for the specific role and company
4. Highlight 2-3 most relevant experiences/skills
5. Explain why you're a good fit
6. Keep it professional but personable
7. Include a strong closing

Return the cover letter as plain text, ready to use. Start with:
"Dear Hiring Manager,"

Do not include markdown formatting."""
        
        cover_letter_text = await llm_service.generate_text(prompt)
        
        # Clean up the response
        if isinstance(cover_letter_text, str):
            # Remove markdown if present
            cover_letter_text = cover_letter_text.strip()
            if cover_letter_text.startswith("```"):
                cover_letter_text = cover_letter_text.split("\n", 1)[1] if "\n" in cover_letter_text else cover_letter_text
                cover_letter_text = cover_letter_text.rsplit("```", 1)[0] if "```" in cover_letter_text else cover_letter_text
        
        # Check if cover letter already exists for this job
        existing_letter = await db.fetch_one(
            "SELECT id FROM cover_letters WHERE user_id = $1 AND job_id = $2",
            current_user["id"], job_id
        )
        
        if existing_letter:
            # Update existing cover letter
            await db.execute(
                """UPDATE cover_letters 
                   SET content = $1, updated_at = NOW()
                   WHERE id = $2""",
                cover_letter_text,
                existing_letter["id"]
            )
            cover_letter_id = existing_letter["id"]
        else:
            # Create new cover letter
            cover_letter_id = await db.fetch_val(
                """INSERT INTO cover_letters (user_id, job_id, content, template_used, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, NOW(), NOW())
                   RETURNING id""",
                current_user["id"],
                job_id,
                cover_letter_text,
                "standard"
            )
        
        return {
            "cover_letter_id": str(cover_letter_id),
            "job_id": job_id,
            "job_title": job.get("title"),
            "company": job.get("company"),
            "content": cover_letter_text,
            "redirect_url": f"/applications/prepare/cover-letter/{cover_letter_id}"
        }
    
    except Exception as e:
        print(f"Error generating cover letter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")


@router.get("/prepare/cv/{cv_id}", response_model=dict)
async def get_tailored_cv(
    cv_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get a tailored CV by ID.
    """
    tailored_cv = await db.fetch_one(
        """SELECT tc.*, j.title as job_title, j.company, j.id as job_id
           FROM tailored_cvs tc
           JOIN jobs j ON tc.job_id = j.id
           WHERE tc.id = $1 AND tc.user_id = $2""",
        cv_id, current_user["id"]
    )
    
    if not tailored_cv:
        raise HTTPException(status_code=404, detail="Tailored CV not found")
    
    # Parse tailored_content JSON
    tailored_content = tailored_cv.get("tailored_content")
    if isinstance(tailored_content, str):
        try:
            tailored_content = json.loads(tailored_content)
        except:
            tailored_content = {}
    
    # Extract HTML content if available
    html_content = None
    if isinstance(tailored_content, dict):
        html_content = tailored_content.get("html_content")
    
    return {
        "id": str(tailored_cv["id"]),
        "job_id": str(tailored_cv["job_id"]),
        "job_title": tailored_cv.get("job_title"),
        "company": tailored_cv.get("company"),
        "tailored_content": tailored_content,
        "html_content": html_content,
        "format": tailored_content.get("format", "json") if isinstance(tailored_content, dict) else "json",
        "emphasis_notes": tailored_cv.get("emphasis_notes"),
        "created_at": tailored_cv.get("created_at"),
        "updated_at": tailored_cv.get("updated_at")
    }


@router.get("/prepare/cv/{cv_id}/download")
async def download_tailored_cv(
    cv_id: str,
    format: str = Query("html", regex="^(html|pdf)$"),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Download a tailored CV as HTML or PDF.
    """
    try:
        tailored_cv = await db.fetch_one(
            """SELECT tc.*, j.title as job_title, j.company, j.id as job_id
               FROM tailored_cvs tc
               JOIN jobs j ON tc.job_id = j.id
               WHERE tc.id = $1 AND tc.user_id = $2""",
            cv_id, current_user["id"]
        )
        
        if not tailored_cv:
            raise HTTPException(status_code=404, detail="Tailored CV not found")
        
        # Parse tailored_content JSON
        tailored_content = tailored_cv.get("tailored_content")
        if isinstance(tailored_content, str):
            try:
                tailored_content = json.loads(tailored_content)
            except json.JSONDecodeError as e:
                print(f"Error parsing tailored_content JSON: {e}")
                tailored_content = {}
        
        # Extract HTML content
        html_content = None
        if isinstance(tailored_content, dict):
            html_content = tailored_content.get("html_content")
        
        if not html_content:
            raise HTTPException(
                status_code=400,
                detail="HTML content not available for this CV. Please regenerate the CV."
            )
        
        # Ensure html_content is a string
        if not isinstance(html_content, str):
            raise HTTPException(
                status_code=400,
                detail="HTML content is not in the correct format. Please regenerate the CV."
            )
        
        # Generate better filename
        job_title = tailored_cv.get("job_title", "CV") or "CV"
        company = tailored_cv.get("company", "") or ""
        safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
        safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
        
        if format == "html":
            filename = f"CV_{safe_title}_{safe_company or 'job'}.html".replace(' ', '_')
            
            # Ensure content is bytes
            if isinstance(html_content, str):
                content_bytes = html_content.encode('utf-8')
            else:
                content_bytes = html_content
            
            return Response(
                content=content_bytes,
                media_type="text/html; charset=utf-8",
                headers={
                    "Content-Disposition": encode_filename_for_header(filename)
                }
            )
        elif format == "pdf":
            # Generate PDF using the agentic service
            try:
                try:
                    from backend.services.cv.agentic_cv_service import get_agentic_cv_service
                except ImportError:
                    from services.cv.agentic_cv_service import get_agentic_cv_service
                cv_service = get_agentic_cv_service()
                pdf_bytes = await cv_service.generate_tailored_cv_pdf(html_content)
                
                if pdf_bytes is None:
                    raise HTTPException(
                        status_code=500,
                        detail="PDF generation failed. Please ensure playwright or xhtml2pdf is installed."
                    )
                
                filename = f"CV_{safe_title}_{safe_company or 'job'}.pdf".replace(' ', '_')
                
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": encode_filename_for_header(filename)
                    }
                )
            except ValueError as e:
                # Handle xhtml2pdf installation or conversion errors
                print(f"PDF generation ValueError: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )
            except Exception as e:
                print(f"PDF generation error: {e}")
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=500,
                    detail=f"PDF generation failed: {str(e)}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Download error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Download failed: {str(e)}"
        )


@router.post("/prepare/cv/{cv_id}/export-pdf")
async def export_cv_to_pdf(
    cv_id: str,
    html_content: str = Body(None, embed=True),
    html_filename: str = Body(None, embed=True),
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Export CV to PDF using HTML content.
    Priority: 1) HTML content from request body, 2) Database, 3) File
    This ensures the PDF uses the most current content, including unsaved edits.
    """
    try:
        # Verify the CV belongs to the user
        tailored_cv = await db.fetch_one(
            """SELECT tc.*, j.title as job_title, j.company
               FROM tailored_cvs tc
               JOIN jobs j ON tc.job_id = j.id
               WHERE tc.id = $1 AND tc.user_id = $2""",
            cv_id, current_user["id"]
        )
        
        if not tailored_cv:
            raise HTTPException(status_code=404, detail="Tailored CV not found")
        
        # Priority 1: Use HTML content from request body if provided (most current)
        html_source = None
        if html_content and isinstance(html_content, str) and len(html_content.strip()) > 0:
            html_source = "request body"
            print(f"Using HTML content from request body for CV {cv_id}, content length: {len(html_content)} characters")
        else:
            # Priority 2: Get HTML from database
            html_content = None
            tailored_content = tailored_cv.get("tailored_content")
            if isinstance(tailored_content, str):
                try:
                    tailored_content = json.loads(tailored_content)
                except json.JSONDecodeError as e:
                    print(f"Error parsing tailored_content JSON: {e}")
                    tailored_content = {}
            
            if isinstance(tailored_content, dict):
                html_content = tailored_content.get("html_content")
        
        if not html_content:
            # Fallback: try reading from file if HTML not in database
            print(f"HTML not found in database for CV {cv_id}, attempting to read from file...")
            from pathlib import Path
            data_cv_dir = Path(__file__).parent.parent / 'data' / 'cv'
            data_cv_dir.mkdir(parents=True, exist_ok=True)
            
            if html_filename:
                html_file_path = data_cv_dir / html_filename
                if html_file_path.exists():
                    with open(html_file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    print(f"Read HTML from file: {html_file_path.name}")
            else:
                # Find the most recent HTML file
                html_files = sorted(
                    data_cv_dir.glob('*.html'),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
                if html_files:
                    html_file_path = html_files[0]
                    with open(html_file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    print(f"Read HTML from most recent file: {html_file_path.name}")
        
        if not html_content:
            raise HTTPException(
                status_code=400,
                detail="HTML content not available for this CV. Please regenerate or save the CV first."
            )
        
        # Ensure html_content is a string
        if not isinstance(html_content, str):
            raise HTTPException(
                status_code=400,
                detail="HTML content is not in the correct format. Please regenerate the CV."
            )
        
        if not html_source:
            if html_content:
                html_source = "database"
            else:
                html_source = "file"
        print(f"Using HTML content from {html_source} for CV {cv_id}, content length: {len(html_content)} characters")
        
        # Generate PDF using the cvhtml2pdf service
        print(f"PDF export requested for CV {cv_id}")
        try:
            try:
                from backend.services.cv.cvhtml2pdf_service import get_cv_html2pdf_service
            except ImportError:
                from services.cv.cvhtml2pdf_service import get_cv_html2pdf_service
            pdf_service = get_cv_html2pdf_service()
            print("Calling convert_to_pdf (Playwright with xhtml2pdf fallback)...")
            pdf_bytes = await pdf_service.convert_to_pdf(html_content, save_debug_files=True)
            print(f"PDF generation completed, size: {len(pdf_bytes) if pdf_bytes else 0} bytes")
            
            if pdf_bytes is None:
                raise HTTPException(
                    status_code=500,
                    detail="PDF generation failed. Please ensure xhtml2pdf is installed."
                )
            
            # Generate filename
            job_title = tailored_cv.get("job_title", "CV") or "CV"
            company = tailored_cv.get("company", "") or ""
            safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
            safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
            filename = f"CV_{safe_title}_{safe_company or 'job'}.pdf".replace(' ', '_')
            
            # Return PDF to frontend
            print(f"Returning PDF to frontend: {filename}, size: {len(pdf_bytes)} bytes")
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": encode_filename_for_header(filename),
                    "Content-Length": str(len(pdf_bytes))
                }
            )
        except ValueError as e:
            # Handle PDF library installation or conversion errors
            error_msg = str(e)
            print(f"PDF generation ValueError: {error_msg}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"PDF generation failed: {error_msg}. Please ensure playwright or xhtml2pdf is installed."
            )
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            print(f"PDF generation error ({error_type}): {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Provide more helpful error messages
            if "playwright" in error_msg.lower():
                detail = f"playwright error: {error_msg}. Please check if playwright is installed: pip install playwright && playwright install chromium"
            elif "xhtml2pdf" in error_msg.lower() or "pisa" in error_msg.lower():
                detail = f"xhtml2pdf error: {error_msg}. Please check if xhtml2pdf is installed: pip install xhtml2pdf"
            else:
                detail = f"PDF generation failed ({error_type}): {error_msg}"
            
            raise HTTPException(
                status_code=500,
                detail=detail
            )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Export PDF error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/prepare/cv/{cv_id}/refine", response_model=dict)
async def refine_tailored_cv(
    cv_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Refine an existing tailored CV without regenerating it completely.
    Validates the CV and refines it iteratively until no issues remain (up to 5 rounds).
    """
    try:
        # Get the existing tailored CV
        tailored_cv = await db.fetch_one(
            """SELECT tc.*, j.title as job_title, j.company, j.description as job_description, j.id as job_id
               FROM tailored_cvs tc
               JOIN jobs j ON tc.job_id = j.id
               WHERE tc.id = $1 AND tc.user_id = $2""",
            cv_id, current_user["id"]
        )
        
        if not tailored_cv:
            raise HTTPException(status_code=404, detail="Tailored CV not found")
        
        # Parse tailored_content JSON
        tailored_content = tailored_cv.get("tailored_content")
        if isinstance(tailored_content, str):
            try:
                tailored_content = json.loads(tailored_content)
            except json.JSONDecodeError:
                tailored_content = {}
        
        # Extract HTML content
        html_content = None
        if isinstance(tailored_content, dict):
            html_content = tailored_content.get("html_content")
        
        if not html_content:
            raise HTTPException(
                status_code=400,
                detail="HTML content not available for this CV. Please regenerate the CV first."
            )
        
        # Get original CV profile for reference
        cv_profile = await db.fetch_one(
            "SELECT parsed_data FROM cv_profiles WHERE id = $1",
            tailored_cv.get("original_cv_profile_id")
        )
        
        if not cv_profile:
            raise HTTPException(
                status_code=400,
                detail="Original CV profile not found. Cannot refine CV."
            )
        
        parsed_data = cv_profile.get("parsed_data")
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError:
                parsed_data = {}
        
        # Use agentic CV service for refinement (always enabled)
        try:
            from backend.services.cv.agentic_cv_service import get_agentic_cv_service
        except ImportError:
            from services.cv.agentic_cv_service import get_agentic_cv_service
        cv_service = get_agentic_cv_service()
        
        result = await cv_service.refine_existing_cv(
            html_content=html_content,
            cv_parsed_data=parsed_data,
            job_description=tailored_cv.get("job_description", ""),
            job_title=tailored_cv.get("job_title", ""),
            company=tailored_cv.get("company", "")
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to refine CV")
            )
        
        # Update the tailored CV with refined content
        refined_html = result["html_content"]
        tailored_data = {
            **tailored_content,
            "html_content": refined_html,
            "refined_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "refinement_rounds": result.get("refinement_rounds", 0),
            "final_quality_score": result.get("final_quality_score", 0)
        }
        
        await db.execute(
            """UPDATE tailored_cvs 
               SET tailored_content = $1, updated_at = NOW()
               WHERE id = $2""",
            json.dumps(tailored_data),
            cv_id
        )
        
        # Include agent steps if available (for agentic CV refinement)
        agent_steps = result.get("agent_steps", [])
        
        return {
            "tailored_cv_id": cv_id,
            "html_content": refined_html,
            "refinement_rounds": result.get("refinement_rounds", 0),
            "final_quality_score": result.get("final_quality_score", 0),
            "success": True,
            "message": f"CV refined successfully after {result.get('refinement_rounds', 0)} rounds",
            "agent_steps": agent_steps
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error refining CV: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refine CV: {str(e)}"
        )


@router.put("/prepare/cv/{cv_id}/save", response_model=dict)
async def save_cv_draft(
    cv_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Save edited CV draft.
    """
    try:
        html_content = request.get("html_content")
        status = request.get("status", "draft")  # "draft" or "final"
        notes = request.get("notes")
        
        if not html_content:
            raise HTTPException(
                status_code=400,
                detail="html_content is required"
            )
        
        # Get existing tailored CV
        tailored_cv = await db.fetch_one(
            "SELECT tailored_content FROM tailored_cvs WHERE id = $1 AND user_id = $2",
            cv_id, current_user["id"]
        )
        
        if not tailored_cv:
            raise HTTPException(status_code=404, detail="Tailored CV not found")
        
        # Parse existing content
        tailored_content = tailored_cv.get("tailored_content")
        if isinstance(tailored_content, str):
            try:
                tailored_content = json.loads(tailored_content)
            except json.JSONDecodeError:
                tailored_content = {}
        
        # Use editor service to update with versioning
        try:
            from backend.services.cv.editor_service import get_cv_editor_service
        except ImportError:
            from services.cv.editor_service import get_cv_editor_service
        editor_service = get_cv_editor_service()
        
        # Update content with edit
        tailored_content = editor_service.update_tailored_content_with_edit(
            tailored_content,
            html_content,
            status
        )
        
        # Save to database
        await db.execute(
            """UPDATE tailored_cvs 
               SET tailored_content = $1, updated_at = NOW()
               WHERE id = $2""",
            json.dumps(tailored_content),
            cv_id
        )
        
        return {
            "success": True,
            "message": f"CV saved as {status}",
            "status": status,
            "html_content": html_content
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving CV draft: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save CV draft: {str(e)}"
        )


@router.post("/prepare/cv/{cv_id}/validate", response_model=dict)
async def validate_edited_cv(
    cv_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Validate edited CV content.
    """
    try:
        html_content = request.get("html_content")
        
        if not html_content:
            raise HTTPException(
                status_code=400,
                detail="html_content is required"
            )
        
        # Get CV and job info
        tailored_cv = await db.fetch_one(
            """SELECT tc.*, j.description as job_description, j.title as job_title, j.company
               FROM tailored_cvs tc
               JOIN jobs j ON tc.job_id = j.id
               WHERE tc.id = $1 AND tc.user_id = $2""",
            cv_id, current_user["id"]
        )
        
        if not tailored_cv:
            raise HTTPException(status_code=404, detail="Tailored CV not found")
        
        # Get original CV profile
        cv_profile = await db.fetch_one(
            "SELECT parsed_data FROM cv_profiles WHERE id = $1",
            tailored_cv.get("original_cv_profile_id")
        )
        
        if not cv_profile:
            raise HTTPException(
                status_code=400,
                detail="Original CV profile not found"
            )
        
        # Format CV text for validation
        parsed_data = cv_profile.get("parsed_data")
        if isinstance(parsed_data, str):
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError:
                parsed_data = {}
        
        try:
            from backend.services.cv.agentic_cv_service import get_agentic_cv_service
        except ImportError:
            from services.cv.agentic_cv_service import get_agentic_cv_service
        cv_service = get_agentic_cv_service()
        cv_text = cv_service._format_cv_text_from_parsed_data(parsed_data)
        
        # Use validation service
        try:
            from backend.services.cv.validation_service import get_cv_validation_service
        except ImportError:
            from services.cv.validation_service import get_cv_validation_service
        validation_service = get_cv_validation_service()
        
        # Quick job analysis if needed
        job_analysis = None
        if tailored_cv.get("job_description"):
            try:
                job_analysis_result = await cv_service._agent_step_analyze_job(
                    tailored_cv.get("job_description", ""),
                    tailored_cv.get("job_title", ""),
                    tailored_cv.get("company", "")
                )
                if job_analysis_result.get("success"):
                    job_analysis = job_analysis_result.get("analysis", {})
            except:
                pass
        
        result = await validation_service.validate_edited_cv(
            html_content=html_content,
            original_cv_text=cv_text,
            job_description=tailored_cv.get("job_description"),
            job_analysis=job_analysis
        )
        
        return {
            "success": True,
            "validation": result.get("validation", {}),
            "warning": result.get("warning")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error validating CV: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate CV: {str(e)}"
        )


@router.post("/prepare/cv/{cv_id}/assist", response_model=dict)
async def ai_assist_cv(
    cv_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    AI-assisted improvement for selected CV content.
    """
    import time
    perf_log = []
    start_time = time.time()
    
    def log_step(step: str):
        now = time.time()
        elapsed = (now - start_time) * 1000  # Convert to ms
        perf_log.append({"step": step, "timestamp": now, "elapsed_ms": elapsed})
        print(f"[AI Action Backend Perf] {step} | Elapsed: {elapsed:.2f}ms | Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))}")
    
    log_step("START: ai_assist_cv endpoint called")
    try:
        log_step("VALIDATION: Starting input validation")
        selection_html = request.get("selection_html")
        intent = request.get("intent", "improve_tone")  # improve_tone, shorten, add_metrics, etc.
        context = request.get("context", {})
        
        # Allow empty selection_html for "write" intent
        if not selection_html and intent.lower() != "write":
            raise HTTPException(
                status_code=400,
                detail="selection_html is required"
            )
        log_step("VALIDATION: Input validation passed")
        
        log_step("DB_QUERY: Fetching CV and job info")
        # Get job info for context
        tailored_cv = await db.fetch_one(
            """SELECT tc.*, j.description as job_description, j.title as job_title, j.company
               FROM tailored_cvs tc
               JOIN jobs j ON tc.job_id = j.id
               WHERE tc.id = $1 AND tc.user_id = $2""",
            cv_id, current_user["id"]
        )
        log_step("DB_QUERY: Database query completed")
        
        if not tailored_cv:
            raise HTTPException(status_code=404, detail="Tailored CV not found")
        
        log_step("CONTEXT: Enhancing context with job info")
        # Enhance context with job info
        if tailored_cv.get("job_description"):
            context["job_description"] = tailored_cv.get("job_description")
        if tailored_cv.get("job_title"):
            context["job_title"] = tailored_cv.get("job_title")
        log_step("CONTEXT: Context enhanced")
        
        log_step("SERVICE: Getting AI assist service")
        # Use AI assist service
        try:
            from backend.services.cv.ai_assist_service import get_ai_assist_service
        except ImportError:
            from services.cv.ai_assist_service import get_ai_assist_service
        assist_service = get_ai_assist_service()
        log_step("SERVICE: AI assist service obtained")
        
        log_step("LLM_CALL: Calling improve_selection")
        result = await assist_service.improve_selection(
            selection_html=selection_html,
            intent=intent,
            context=context
        )
        log_step("LLM_CALL: improve_selection completed")
        
        # Log summary
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        print(f"[AI Action Backend Perf] ===== SUMMARY ======")
        print(f"[AI Action Backend Perf] Total time: {total_time:.2f}ms ({total_time/1000:.2f}s)")
        for i, log in enumerate(perf_log):
            prev_time = perf_log[i-1]["timestamp"] if i > 0 else start_time
            step_duration = (log["timestamp"] - prev_time) * 1000
            print(f"[AI Action Backend Perf] {log['step']} | Step duration: {step_duration:.2f}ms | Cumulative: {log['elapsed_ms']:.2f}ms")
        print(f"[AI Action Backend Perf] ====================")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI assist: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assist with CV: {str(e)}"
        )


@router.post("/prepare/cv/{cv_id}/assist/stream")
async def ai_assist_cv_stream(
    cv_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Streaming AI-assisted improvement for selected CV content.
    Sends Server-Sent Events (SSE) so the frontend can display partial output.
    """
    try:
        selection_html = request.get("selection_html")
        intent = request.get("intent", "improve_tone")
        context = request.get("context", {}) or {}

        if not selection_html:
            raise HTTPException(
                status_code=400,
                detail="selection_html is required"
            )

        tailored_cv = await db.fetch_one(
            """SELECT tc.*, j.description as job_description, j.title as job_title, j.company
               FROM tailored_cvs tc
               JOIN jobs j ON tc.job_id = j.id
               WHERE tc.id = $1 AND tc.user_id = $2""",
            cv_id, current_user["id"]
        )

        if not tailored_cv:
            raise HTTPException(status_code=404, detail="Tailored CV not found")

        if tailored_cv.get("job_description"):
            context["job_description"] = tailored_cv.get("job_description")
        if tailored_cv.get("job_title"):
            context["job_title"] = tailored_cv.get("job_title")

        try:
            from backend.services.cv.ai_assist_service import get_ai_assist_service
        except ImportError:
            from services.cv.ai_assist_service import get_ai_assist_service

        assist_service = get_ai_assist_service()
        stream_generator = assist_service.stream_improvement(
            selection_html=selection_html,
            intent=intent,
            context=context
        )

        async def event_generator():
            try:
                # Send initial keep-alive to establish connection
                yield ": keep-alive\n\n"
                
                chunk_count = 0
                async for chunk in stream_generator:
                    chunk_count += 1
                    chunk_json = json.dumps(chunk)
                    yield f"data: {chunk_json}\n\n"
                
                # If no chunks were received, send an error
                if chunk_count == 0:
                    error_payload = {"error": "No data received from AI service"}
                    yield f"data: {json.dumps(error_payload)}\n\n"
                
                yield "data: [DONE]\n\n"
            except Exception as stream_error:
                print(f"Error in event generator: {stream_error}")
                import traceback
                traceback.print_exc()
                error_payload = {"error": str(stream_error)}
                yield f"data: {json.dumps(error_payload)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI assist stream: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stream CV assist: {str(e)}"
        )


@router.get("/prepare/cover-letter/{letter_id}", response_model=dict)
async def get_cover_letter(
    letter_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Get a cover letter by ID.
    """
    cover_letter = await db.fetch_one(
        """SELECT cl.*, j.title as job_title, j.company, j.id as job_id
           FROM cover_letters cl
           JOIN jobs j ON cl.job_id = j.id
           WHERE cl.id = $1 AND cl.user_id = $2""",
        letter_id, current_user["id"]
    )
    
    if not cover_letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    
    return {
        "id": str(cover_letter["id"]),
        "job_id": str(cover_letter["job_id"]),
        "job_title": cover_letter.get("job_title"),
        "company": cover_letter.get("company"),
        "content": cover_letter.get("content"),
        "template_used": cover_letter.get("template_used"),
        "created_at": cover_letter.get("created_at"),
        "updated_at": cover_letter.get("updated_at")
    }


@router.put("/prepare/cover-letter/{letter_id}", response_model=dict)
async def update_cover_letter(
    letter_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Update a cover letter's content.
    """
    # Verify ownership
    cover_letter = await db.fetch_one(
        "SELECT id FROM cover_letters WHERE id = $1 AND user_id = $2",
        letter_id, current_user["id"]
    )
    
    if not cover_letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    
    # Get content from request body
    content = request.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # Update content
    await db.execute(
        "UPDATE cover_letters SET content = $1, updated_at = NOW() WHERE id = $2",
        content, letter_id
    )
    
    # Return updated cover letter
    updated = await db.fetch_one(
        """SELECT cl.*, j.title as job_title, j.company, j.id as job_id
           FROM cover_letters cl
           JOIN jobs j ON cl.job_id = j.id
           WHERE cl.id = $1""",
        letter_id
    )
    
    return {
        "id": str(updated["id"]),
        "job_id": str(updated["job_id"]),
        "job_title": updated.get("job_title"),
        "company": updated.get("company"),
        "content": updated.get("content"),
        "template_used": updated.get("template_used"),
        "updated_at": updated.get("updated_at")
    }


@router.get("/{job_id}/prepare/status", response_model=dict)
async def get_preparation_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """
    Check if tailored CV or cover letter exists for a job.
    Returns IDs if they exist.
    """
    # Check for tailored CV
    tailored_cv = await db.fetch_one(
        "SELECT id FROM tailored_cvs WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )
    
    # Check for cover letter
    cover_letter = await db.fetch_one(
        "SELECT id FROM cover_letters WHERE user_id = $1 AND job_id = $2",
        current_user["id"], job_id
    )
    
    return {
        "job_id": job_id,
        "has_tailored_cv": tailored_cv is not None,
        "tailored_cv_id": str(tailored_cv["id"]) if tailored_cv else None,
        "has_cover_letter": cover_letter is not None,
        "cover_letter_id": str(cover_letter["id"]) if cover_letter else None
    }

