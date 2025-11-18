"""
Interview API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid
import json

from models.interview import (
    StartSessionRequest,
    InterviewSession,
    QuestionWithContext,
    SubmitAnswerRequest,
    EvaluationResult,
    InterviewResponse,
    InterviewQuestion,
    SessionHistory,
    SessionDetail,
    PerformanceAnalytics,
    SessionStatus,
    EvaluationScores
)
from api.auth import get_current_user
from database.postgres_client import PostgresClient, get_db
from services.interview_service import interview_service

router = APIRouter()


@router.post("/sessions/start", response_model=InterviewSession)
async def start_interview_session(
    request: StartSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """Start a new interview practice session."""
    session_id = str(uuid.uuid4())
    user_id = current_user["id"]
    started_at = datetime.utcnow()
    
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    try:
        session_row = await db.fetch_one(
            """INSERT INTO interview_sessions 
               (id, user_id, role_type, domain, job_id, status, total_questions, completed_questions, started_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
               RETURNING *""",
            session_id, user_id, request.role_type, request.domain, request.job_id, 
            "active", request.total_questions, 0, started_at
        )
        
        if not session_row:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        # Convert database row to dict and handle datetime
        session_dict = dict(session_row)
        if session_dict.get("started_at"):
            session_dict["started_at"] = session_dict["started_at"].isoformat() if hasattr(session_dict["started_at"], "isoformat") else str(session_dict["started_at"])
        if session_dict.get("completed_at"):
            session_dict["completed_at"] = session_dict["completed_at"].isoformat() if hasattr(session_dict["completed_at"], "isoformat") else str(session_dict["completed_at"])
        
        return InterviewSession(**session_dict)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating interview session: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions/{session_id}/next-question", response_model=QuestionWithContext)
async def get_next_question(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """Get the next question for the current session."""
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    # Get session
    session_row = await db.fetch_one(
        "SELECT * FROM interview_sessions WHERE id = $1 AND user_id = $2",
        session_id, current_user["id"]
    )
    
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = dict(session_row)
    
    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Session is not active")
    
    if session["completed_questions"] >= session["total_questions"]:
        # Mark session as completed
        await db.execute(
            """UPDATE interview_sessions 
               SET status = $1, completed_at = $2 
               WHERE id = $3""",
            "completed", datetime.utcnow(), session_id
        )
        raise HTTPException(status_code=400, detail="Session already completed")
    
    # Get answered question IDs
    answered_rows = await db.fetch_all(
        "SELECT question_id FROM interview_responses WHERE session_id = $1",
        session_id
    )
    answered_ids = [r["question_id"] for r in answered_rows] if answered_rows else []
    
    # Build query for available questions
    # Start with base conditions
    conditions = ["is_active = TRUE"]
    params = []
    param_num = 1
    
    # Filter by role_type - include questions that match the role OR are "Both"
    if session["role_type"] != "Both":
        conditions.append(f"(role_type = ${param_num} OR role_type = 'Both')")
        params.append(session["role_type"])
        param_num += 1
    # If role_type is "Both", we want questions with role_type = "Both" OR any specific role
    # Actually, if role_type is "Both", we should accept all questions
    # So we don't add a condition for role_type when it's "Both"
    
    # Filter by domain - include questions that match the domain OR are "General"
    if session["domain"] != "General":
        conditions.append(f"(domain = ${param_num} OR domain = 'General')")
        params.append(session["domain"])
        param_num += 1
    # If domain is "General", we want questions with domain = "General" OR any specific domain
    # Actually, if domain is "General", we should accept all questions
    # So we don't add a condition for domain when it's "General"
    
    # Exclude already answered questions
    if answered_ids:
        # Use array comparison for UUIDs
        conditions.append(f"id != ALL(${param_num}::uuid[])")
        params.append(answered_ids)
        param_num += 1
    
    query = f"SELECT * FROM interview_questions WHERE {' AND '.join(conditions)} LIMIT 1"
    
    try:
        question_row = await db.fetch_one(query, *params)
    except Exception as query_err:
        print(f"Query error: {query_err}")
        print(f"Query: {query}")
        print(f"Params: {params}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database query error: {str(query_err)}")
    
    if not question_row:
        raise HTTPException(status_code=404, detail="No more questions available")
    
    question_dict = dict(question_row)
    
    # Convert UUID to string if needed
    if "id" in question_dict and question_dict["id"]:
        question_dict["id"] = str(question_dict["id"])
    
    # Map database fields to model fields
    # Database has 'question_type' but model expects 'category'
    if "question_type" in question_dict and "category" not in question_dict:
        question_dict["category"] = question_dict.pop("question_type", "technical")
    
    # Ensure category is a valid enum value (default to technical if invalid)
    if "category" in question_dict:
        valid_categories = ["technical", "behavioral", "case_study", "situational", "coding"]
        if question_dict["category"] not in valid_categories:
            question_dict["category"] = "technical"
    
    # Ensure difficulty is valid (default to beginner if invalid)
    if "difficulty" in question_dict:
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if question_dict["difficulty"] not in valid_difficulties:
            question_dict["difficulty"] = "beginner"
    
    # Convert datetime to ISO format if needed
    if question_dict.get("created_at") and hasattr(question_dict["created_at"], "isoformat"):
        question_dict["created_at"] = question_dict["created_at"].isoformat()
    
    # Ensure all required fields are present with defaults
    if "is_active" not in question_dict:
        question_dict["is_active"] = True
    
    # Remove database-specific fields that aren't in the model
    # Keep only fields that the InterviewQuestion model expects
    expected_fields = ["id", "question_text", "role_type", "domain", "category", "difficulty", 
                      "ideal_answer", "metadata", "is_active", "created_at"]
    question_dict = {k: v for k, v in question_dict.items() if k in expected_fields}
    
    try:
        question = InterviewQuestion(**question_dict)
    except Exception as model_err:
        print(f"Error creating InterviewQuestion model: {model_err}")
        print(f"Question dict keys: {list(question_dict.keys())}")
        print(f"Question dict: {question_dict}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create question model: {str(model_err)}")
    
    progress = (session["completed_questions"] / session["total_questions"]) * 100
    
    return QuestionWithContext(
        question=question,
        question_number=session["completed_questions"] + 1,
        total_questions=session["total_questions"],
        session_progress=progress
    )


@router.post("/sessions/{session_id}/submit-answer", response_model=EvaluationResult)
async def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """Submit an answer and get AI evaluation."""
    try:
        # Ensure database connection is established
        if db.pool is None:
            await db.connect()
        
        # Get session
        session_row = await db.fetch_one(
            "SELECT * FROM interview_sessions WHERE id = $1 AND user_id = $2",
            session_id, current_user["id"]
        )
        
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = dict(session_row)
        
        # Get question
        question_row = await db.fetch_one(
            "SELECT * FROM interview_questions WHERE id = $1",
            request.question_id
        )
        
        if not question_row:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Format question for model
        q_dict = dict(question_row)
        if "question_type" in q_dict and "category" not in q_dict:
            q_dict["category"] = q_dict.pop("question_type", "technical")
        if q_dict.get("id"):
            q_dict["id"] = str(q_dict["id"])
        if q_dict.get("created_at") and hasattr(q_dict["created_at"], "isoformat"):
            q_dict["created_at"] = q_dict["created_at"].isoformat()
        
        question = InterviewQuestion(**q_dict)

        try:
            evaluation = await interview_service.evaluate_answer(
                question=question,
                user_answer=request.user_answer,
                knowledge_context=None
            )
        except Exception as eval_err:
            print(f"Error evaluating answer: {eval_err}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to evaluate answer: {str(eval_err)}")

        # Save response to database
        response_id = str(uuid.uuid4())
        submitted_at = datetime.utcnow()
        
        # Prepare data for insertion
        strengths_list = evaluation.get("strengths", []) or []
        improvements_list = evaluation.get("improvements", []) or []
        
        # Ensure strengths and improvements are lists
        if not isinstance(strengths_list, list):
            strengths_list = [str(strengths_list)] if strengths_list else []
        if not isinstance(improvements_list, list):
            improvements_list = [str(improvements_list)] if improvements_list else []
        
        try:
            await db.execute(
                """INSERT INTO interview_responses 
                   (id, session_id, question_id, user_answer, evaluation_scores, feedback, strengths, improvements, submitted_at)
                   VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)""",
                response_id, session_id, request.question_id, request.user_answer,
                json.dumps(evaluation), evaluation.get("feedback", "") or "",
                strengths_list, improvements_list,
                submitted_at
            )
        except Exception as db_err:
            print(f"Database insert error: {db_err}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to save response: {str(db_err)}")
        
        # Get response for return
        try:
            response_row = await db.fetch_one(
                "SELECT * FROM interview_responses WHERE id = $1",
                response_id
            )
            
            if not response_row:
                raise HTTPException(status_code=500, detail="Failed to retrieve saved response")
            
            response_dict = dict(response_row)
            
            # Convert UUIDs to strings
            if response_dict.get("id"):
                response_dict["id"] = str(response_dict["id"])
            if response_dict.get("session_id"):
                response_dict["session_id"] = str(response_dict["session_id"])
            if response_dict.get("question_id"):
                response_dict["question_id"] = str(response_dict["question_id"])
            
            # Convert datetime
            if response_dict.get("submitted_at") and hasattr(response_dict["submitted_at"], "isoformat"):
                response_dict["submitted_at"] = response_dict["submitted_at"].isoformat()
            
            # Handle evaluation_scores - it might be JSONB (dict) or string
            eval_scores = response_dict.get("evaluation_scores")
            if eval_scores:
                if isinstance(eval_scores, str):
                    try:
                        eval_scores = json.loads(eval_scores)
                    except:
                        eval_scores = {}
                # Convert to EvaluationScores model if it's a dict
                if isinstance(eval_scores, dict):
                    try:
                        # Map the evaluation dict to EvaluationScores model fields
                        scores_dict = {
                            "overall_score": eval_scores.get("overall_score", 3.0),
                            "relevance_score": eval_scores.get("relevance_score", 3.0),
                            "completeness_score": eval_scores.get("completeness_score", 3.0),
                            "technical_accuracy_score": eval_scores.get("technical_accuracy_score", 3.0),
                            "communication_score": eval_scores.get("communication_score", 3.0)
                        }
                        response_dict["evaluation_scores"] = EvaluationScores(**scores_dict)
                    except Exception as score_err:
                        print(f"Warning: Could not convert evaluation_scores to model: {score_err}")
                        print(f"Eval scores dict: {eval_scores}")
                        # Set to None if conversion fails
                        response_dict["evaluation_scores"] = None
                else:
                    response_dict["evaluation_scores"] = None
            else:
                response_dict["evaluation_scores"] = None
            
            # Ensure strengths and improvements are lists
            if response_dict.get("strengths") and not isinstance(response_dict["strengths"], list):
                response_dict["strengths"] = [str(response_dict["strengths"])]
            if response_dict.get("improvements") and not isinstance(response_dict["improvements"], list):
                response_dict["improvements"] = [str(response_dict["improvements"])]
            
            response_obj = InterviewResponse(**response_dict)
        except Exception as resp_err:
            print(f"Error creating response object: {resp_err}")
            print(f"Response dict: {response_dict if 'response_dict' in locals() else 'N/A'}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to create response object: {str(resp_err)}")
        
        completed_questions = session["completed_questions"] + 1
        is_session_complete = completed_questions >= session["total_questions"]
        
        # Calculate average score
        all_response_rows = await db.fetch_all(
            "SELECT evaluation_scores FROM interview_responses WHERE session_id = $1",
            session_id
        )
        scores = []
        for row in all_response_rows:
            scores_data = row.get("evaluation_scores")
            if scores_data and isinstance(scores_data, dict):
                scores.append(scores_data.get("overall_score", 0))
            elif scores_data:
                try:
                    scores_dict = json.loads(scores_data) if isinstance(scores_data, str) else scores_data
                    scores.append(scores_dict.get("overall_score", 0))
                except:
                    pass
        avg_score = sum(scores) / len(scores) if scores else None
        
        # Update session
        if is_session_complete:
            await db.execute(
                """UPDATE interview_sessions 
                   SET completed_questions = $1, avg_score = $2, status = $3, completed_at = $4
                   WHERE id = $5""",
                completed_questions, avg_score, "completed", datetime.utcnow(), session_id
            )
            # TODO: Update analytics table if needed
        else:
            await db.execute(
                """UPDATE interview_sessions 
                   SET completed_questions = $1, avg_score = $2
                   WHERE id = $3""",
                completed_questions, avg_score, session_id
            )
        
        next_question = None
        if not is_session_complete:
            try:
                next_q_result = await get_next_question(session_id, current_user, db)
                next_question = next_q_result.question
            except:
                pass

        return EvaluationResult(
            response=response_obj,
            question=question,
            is_session_complete=is_session_complete,
            next_question=next_question
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in submit_answer: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.get("/sessions/history", response_model=SessionHistory)
async def get_session_history(
    current_user: dict = Depends(get_current_user),
    limit: int = 10,
    db: PostgresClient = Depends(get_db)
):
    """Get user's interview session history."""
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    rows = await db.fetch_all(
        "SELECT * FROM interview_sessions WHERE user_id = $1 ORDER BY started_at DESC LIMIT $2",
        current_user["id"], limit
    )
    
    sessions = []
    for row in rows:
        session_dict = dict(row)
        # Convert datetime to ISO format
        if session_dict.get("started_at") and hasattr(session_dict["started_at"], "isoformat"):
            session_dict["started_at"] = session_dict["started_at"].isoformat()
        if session_dict.get("completed_at") and hasattr(session_dict["completed_at"], "isoformat"):
            session_dict["completed_at"] = session_dict["completed_at"].isoformat()
        # Convert UUID to string
        if session_dict.get("id"):
            session_dict["id"] = str(session_dict["id"])
        if session_dict.get("user_id"):
            session_dict["user_id"] = str(session_dict["user_id"])
        if session_dict.get("job_id"):
            session_dict["job_id"] = str(session_dict["job_id"])
        sessions.append(InterviewSession(**session_dict))
    
    # Calculate average performance only if there are sessions with scores
    sessions_with_scores = [s.avg_score for s in sessions if s.avg_score]
    avg_performance = sum(sessions_with_scores) / len(sessions_with_scores) if sessions_with_scores else None

    return SessionHistory(
        sessions=sessions,
        total_sessions=len(sessions),
        avg_performance=avg_performance
    )


@router.get("/sessions/job/{job_id}", response_model=SessionHistory)
async def get_sessions_by_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """Get all interview sessions (active and completed) for a specific job."""
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    rows = await db.fetch_all(
        "SELECT * FROM interview_sessions WHERE user_id = $1 AND job_id = $2 ORDER BY started_at DESC",
        current_user["id"], job_id
    )
    
    sessions = []
    for row in rows:
        session_dict = dict(row)
        # Convert datetime to ISO format
        if session_dict.get("started_at") and hasattr(session_dict["started_at"], "isoformat"):
            session_dict["started_at"] = session_dict["started_at"].isoformat()
        if session_dict.get("completed_at") and hasattr(session_dict["completed_at"], "isoformat"):
            session_dict["completed_at"] = session_dict["completed_at"].isoformat()
        # Convert UUID to string
        if session_dict.get("id"):
            session_dict["id"] = str(session_dict["id"])
        if session_dict.get("user_id"):
            session_dict["user_id"] = str(session_dict["user_id"])
        if session_dict.get("job_id"):
            session_dict["job_id"] = str(session_dict["job_id"])
        sessions.append(InterviewSession(**session_dict))
    
    # Calculate average performance only if there are sessions with scores
    sessions_with_scores = [s.avg_score for s in sessions if s.avg_score]
    avg_performance = sum(sessions_with_scores) / len(sessions_with_scores) if sessions_with_scores else None

    return SessionHistory(
        sessions=sessions,
        total_sessions=len(sessions),
        avg_performance=avg_performance
    )


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """Get detailed information about a specific session."""
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    # Convert string UUIDs to UUID objects for proper database comparison
    try:
        session_uuid = uuid.UUID(session_id)
        user_uuid = uuid.UUID(current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")
    
    # Get session
    session_row = await db.fetch_one(
        "SELECT * FROM interview_sessions WHERE id = $1 AND user_id = $2",
        session_uuid, user_uuid
    )
    
    if not session_row:
        # Additional debug: check if session exists without user_id check
        try:
            check_row = await db.fetch_one(
                "SELECT id, user_id, status FROM interview_sessions WHERE id = $1",
                session_uuid
            )
            if check_row:
                check_user_id = str(check_row.get('user_id', ''))
                current_user_id = str(current_user['id'])
                print(f"Session exists but user_id mismatch. Session user_id: {check_user_id}, Current user_id: {current_user_id}")
                if check_user_id != current_user_id:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Access denied. This session belongs to a different user."
                    )
            else:
                print(f"Session with id {session_id} does not exist in database")
                raise HTTPException(status_code=404, detail="Session not found")
        except HTTPException:
            raise
        except Exception as check_err:
            print(f"Error checking session existence: {check_err}")
            raise HTTPException(status_code=404, detail="Session not found")
    
    # Get responses
    response_rows = await db.fetch_all(
        "SELECT * FROM interview_responses WHERE session_id = $1",
        session_uuid
    )
    
    responses = []
    question_ids = []
    for row in response_rows:
        resp_dict = dict(row)
        # Convert UUIDs to strings
        if resp_dict.get("id"):
            resp_dict["id"] = str(resp_dict["id"])
        if resp_dict.get("session_id"):
            resp_dict["session_id"] = str(resp_dict["session_id"])
        if resp_dict.get("question_id"):
            resp_dict["question_id"] = str(resp_dict["question_id"])
            question_ids.append(resp_dict["question_id"])
        # Convert datetime
        if resp_dict.get("submitted_at") and hasattr(resp_dict["submitted_at"], "isoformat"):
            resp_dict["submitted_at"] = resp_dict["submitted_at"].isoformat()
        # Handle evaluation_scores - it might be JSONB (dict) or string
        eval_scores = resp_dict.get("evaluation_scores")
        if eval_scores:
            if isinstance(eval_scores, str):
                try:
                    eval_scores = json.loads(eval_scores)
                except (json.JSONDecodeError, TypeError):
                    eval_scores = {}
            # Convert to EvaluationScores model if it's a dict
            if isinstance(eval_scores, dict):
                try:
                    # Map the evaluation dict to EvaluationScores model fields
                    scores_dict = {
                        "overall_score": eval_scores.get("overall_score", 3.0),
                        "relevance_score": eval_scores.get("relevance_score", 3.0),
                        "completeness_score": eval_scores.get("completeness_score", 3.0),
                        "technical_accuracy_score": eval_scores.get("technical_accuracy_score", 3.0),
                        "communication_score": eval_scores.get("communication_score", 3.0)
                    }
                    resp_dict["evaluation_scores"] = EvaluationScores(**scores_dict)
                except Exception as score_err:
                    print(f"Warning: Could not convert evaluation_scores to model: {score_err}")
                    print(f"Eval scores dict: {eval_scores}")
                    # Set to None if conversion fails
                    resp_dict["evaluation_scores"] = None
            else:
                resp_dict["evaluation_scores"] = None
        else:
            resp_dict["evaluation_scores"] = None
        
        # Ensure strengths and improvements are lists
        if resp_dict.get("strengths") and not isinstance(resp_dict["strengths"], list):
            resp_dict["strengths"] = [str(resp_dict["strengths"])]
        if resp_dict.get("improvements") and not isinstance(resp_dict["improvements"], list):
            resp_dict["improvements"] = [str(resp_dict["improvements"])]
        
        responses.append(InterviewResponse(**resp_dict))
    
    # Get questions
    questions = []
    if question_ids:
        placeholders = ",".join([f"${i+1}" for i in range(len(question_ids))])
        question_rows = await db.fetch_all(
            f"SELECT * FROM interview_questions WHERE id IN ({placeholders})",
            *question_ids
        )
        for row in question_rows:
            q_dict = dict(row)
            # Map question_type to category
            if "question_type" in q_dict and "category" not in q_dict:
                q_dict["category"] = q_dict.pop("question_type", "technical")
            # Convert UUID and datetime
            if q_dict.get("id"):
                q_dict["id"] = str(q_dict["id"])
            if q_dict.get("created_at") and hasattr(q_dict["created_at"], "isoformat"):
                q_dict["created_at"] = q_dict["created_at"].isoformat()
            questions.append(InterviewQuestion(**q_dict))
    
    # Format session
    session_dict = dict(session_row)
    if session_dict.get("id"):
        session_dict["id"] = str(session_dict["id"])
    if session_dict.get("user_id"):
        session_dict["user_id"] = str(session_dict["user_id"])
    if session_dict.get("job_id"):
        session_dict["job_id"] = str(session_dict["job_id"])
    if session_dict.get("started_at") and hasattr(session_dict["started_at"], "isoformat"):
        session_dict["started_at"] = session_dict["started_at"].isoformat()
    if session_dict.get("completed_at") and hasattr(session_dict["completed_at"], "isoformat"):
        session_dict["completed_at"] = session_dict["completed_at"].isoformat()
    
    return SessionDetail(
        session=InterviewSession(**session_dict),
        responses=responses,
        questions=questions
    )


@router.get("/analytics", response_model=List[PerformanceAnalytics])
async def get_performance_analytics(
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """Get performance analytics across all domains."""
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    rows = await db.fetch_all(
        "SELECT * FROM interview_performance_analytics WHERE user_id = $1",
        current_user["id"]
    )
    
    if not rows:
        return []
    
    analytics = []
    for row in rows:
        a_dict = dict(row)
        # Convert UUIDs to strings
        if a_dict.get("id"):
            a_dict["id"] = str(a_dict["id"])
        if a_dict.get("user_id"):
            a_dict["user_id"] = str(a_dict["user_id"])
        # Convert datetime
        if a_dict.get("last_practice_date") and hasattr(a_dict["last_practice_date"], "isoformat"):
            a_dict["last_practice_date"] = a_dict["last_practice_date"].isoformat()
        if a_dict.get("created_at") and hasattr(a_dict["created_at"], "isoformat"):
            a_dict["created_at"] = a_dict["created_at"].isoformat()
        if a_dict.get("updated_at") and hasattr(a_dict["updated_at"], "isoformat"):
            a_dict["updated_at"] = a_dict["updated_at"].isoformat()
        analytics.append(PerformanceAnalytics(**a_dict))
    
    return analytics


@router.get("/questions", response_model=List[InterviewQuestion])
async def get_questions(
    role_type: Optional[str] = None,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 20,
    db: PostgresClient = Depends(get_db)
):
    """Browse available interview questions."""
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    # Build query
    conditions = ["is_active = TRUE"]
    params = []
    param_num = 1
    
    if role_type:
        conditions.append(f"(role_type = ${param_num} OR role_type = 'Both')")
        params.append(role_type)
        param_num += 1
    
    if domain:
        conditions.append(f"(domain = ${param_num} OR domain = 'General')")
        params.append(domain)
        param_num += 1
    
    if difficulty:
        conditions.append(f"difficulty = ${param_num}")
        params.append(difficulty)
        param_num += 1
    
    query = f"SELECT * FROM interview_questions WHERE {' AND '.join(conditions)} LIMIT ${param_num}"
    params.append(limit)
    
    rows = await db.fetch_all(query, *params)
    
    questions = []
    for row in rows:
        q_dict = dict(row)
        # Map question_type to category
        if "question_type" in q_dict and "category" not in q_dict:
            q_dict["category"] = q_dict.pop("question_type", "technical")
        # Convert UUID and datetime
        if q_dict.get("id"):
            q_dict["id"] = str(q_dict["id"])
        if q_dict.get("created_at") and hasattr(q_dict["created_at"], "isoformat"):
            q_dict["created_at"] = q_dict["created_at"].isoformat()
        questions.append(InterviewQuestion(**q_dict))
    
    return questions


@router.post("/sessions/{session_id}/abandon")
async def abandon_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: PostgresClient = Depends(get_db)
):
    """Mark a session as abandoned."""
    # Ensure database connection is established
    if db.pool is None:
        await db.connect()
    
    result = await db.execute(
        "UPDATE interview_sessions SET status = $1 WHERE id = $2 AND user_id = $3",
        "abandoned", session_id, current_user["id"]
    )
    
    # Check if any rows were updated
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session abandoned"}
