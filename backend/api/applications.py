"""
Application tracking API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import os
import json

from models.application import (
    ApplicationCreate, Application, ApplicationWithJob, ApplicationStatus,
    ApplicationUpdate, ApplicationStatusEnum
)
from api.auth import get_current_user
from database.postgres_client import get_db, PostgresClient
import sys
import os

# Import LLM service from jobs-finder directory
services_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'jobs-finder')
sys.path.insert(0, services_path)
from llm_service import llm_service

router = APIRouter()

# Valid statuses
VALID_STATUSES = [s.value for s in ApplicationStatusEnum]


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
    Generate a tailored CV for a specific job.
    Highlights relevant experience and skills based on job requirements.
    """
    # Get job details
    job = await db.fetch_one(
        "SELECT id, title, company, description FROM jobs WHERE id = $1",
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
    
    if not parsed_data:
        raise HTTPException(
            status_code=400,
            detail="CV data is not properly parsed. Please re-upload your CV."
        )
    
    # Use LLM to tailor CV
    try:
        prompt = f"""You are a professional resume writer. Tailor this CV/resume for the following job:

Job Title: {job.get('title', '')}
Company: {job.get('company', '')}
Job Description:
{job.get('description', '')[:2000]}

User's CV Data:
{json.dumps(parsed_data, indent=2)[:3000]}

Instructions:
1. Highlight and reorder sections to emphasize relevant experience, skills, and achievements
2. Keep all original information but emphasize what matches the job requirements
3. Add a tailored professional summary at the top (2-3 sentences)
4. Reorder work experience to put most relevant first
5. Highlight relevant skills prominently
6. Keep the same structure and format

Return a JSON object with:
- "tailored_summary": The new professional summary
- "reordered_experience": Array of work experiences in new order with "emphasis_notes" for each
- "highlighted_skills": Array of skills to emphasize with "relevance_reason"
- "emphasis_notes": Overall explanation of what was emphasized and why

Return ONLY valid JSON, no markdown."""
        
        response = await llm_service.generate_text(prompt)
        
        # Parse LLM response
        if isinstance(response, str):
            # Try to extract JSON from response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            try:
                tailored_data = json.loads(response)
            except:
                # Fallback: create basic tailored structure
                tailored_data = {
                    "tailored_summary": f"Experienced professional seeking {job.get('title', 'position')} at {job.get('company', '')}",
                    "reordered_experience": parsed_data.get("work_experience", []),
                    "highlighted_skills": parsed_data.get("skills", {}).get("technical", [])[:5],
                    "emphasis_notes": "CV tailored to match job requirements"
                }
        else:
            tailored_data = response
        
        # Check if tailored CV already exists for this job
        existing_cv = await db.fetch_one(
            "SELECT id FROM tailored_cvs WHERE user_id = $1 AND job_id = $2",
            current_user["id"], job_id
        )
        
        if existing_cv:
            # Update existing tailored CV
            await db.execute(
                """UPDATE tailored_cvs 
                   SET tailored_content = $1, emphasis_notes = $2, updated_at = NOW()
                   WHERE id = $3""",
                json.dumps(tailored_data),
                tailored_data.get("emphasis_notes", "CV tailored to match job requirements"),
                existing_cv["id"]
            )
            tailored_cv_id = existing_cv["id"]
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
                tailored_data.get("emphasis_notes", "CV tailored to match job requirements")
            )
        
        return {
            "tailored_cv_id": str(tailored_cv_id),
            "job_id": job_id,
            "job_title": job.get("title"),
            "company": job.get("company"),
            "tailored_data": tailored_data,
            "original_cv_id": str(cv_profile["id"]),
            "redirect_url": f"/applications/prepare/cv/{tailored_cv_id}"
        }
    
    except Exception as e:
        print(f"Error generating tailored CV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate tailored CV: {str(e)}")


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
    
    return {
        "id": str(tailored_cv["id"]),
        "job_id": str(tailored_cv["job_id"]),
        "job_title": tailored_cv.get("job_title"),
        "company": tailored_cv.get("company"),
        "tailored_content": tailored_content,
        "emphasis_notes": tailored_cv.get("emphasis_notes"),
        "created_at": tailored_cv.get("created_at"),
        "updated_at": tailored_cv.get("updated_at")
    }


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

