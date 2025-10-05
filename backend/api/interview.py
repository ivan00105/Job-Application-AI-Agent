"""
Interview API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid

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
from models.user import User
from api.auth import get_current_user
from database.supabase_client import get_supabase
from services.interview_service import interview_service

router = APIRouter()


@router.post("/sessions/start", response_model=InterviewSession)
async def start_interview_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Start a new interview practice session."""
    supabase = get_supabase()

    session_data = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "role_type": request.role_type,
        "domain": request.domain,
        "job_id": request.job_id,
        "status": "active",
        "total_questions": request.total_questions,
        "completed_questions": 0,
        "started_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("interview_sessions").insert(session_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create session")

    return InterviewSession(**result.data[0])


@router.get("/sessions/{session_id}/next-question", response_model=QuestionWithContext)
async def get_next_question(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the next question for the current session."""
    supabase = get_supabase()

    session_result = supabase.table("interview_sessions").select("*").eq("id", session_id).eq("user_id", current_user.id).single().execute()

    if not session_result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_result.data

    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    if session["completed_questions"] >= session["total_questions"]:
        supabase.table("interview_sessions").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", session_id).execute()
        raise HTTPException(status_code=400, detail="Session already completed")

    answered_questions = supabase.table("interview_responses").select("question_id").eq("session_id", session_id).execute()
    answered_ids = [r["question_id"] for r in (answered_questions.data or [])]

    query = supabase.table("interview_questions").select("*").eq("is_active", True)

    if session["role_type"] != "Both":
        query = query.in_("role_type", [session["role_type"], "Both"])

    if session["domain"] != "General":
        query = query.in_("domain", [session["domain"], "General"])

    if answered_ids:
        query = query.not_.in_("id", answered_ids)

    questions_result = query.limit(1).execute()

    if not questions_result.data:
        raise HTTPException(status_code=404, detail="No more questions available")

    question_data = questions_result.data[0]
    question = InterviewQuestion(**question_data)

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
    current_user: User = Depends(get_current_user)
):
    """Submit an answer and get AI evaluation."""
    supabase = get_supabase()

    session_result = supabase.table("interview_sessions").select("*").eq("id", session_id).eq("user_id", current_user.id).single().execute()

    if not session_result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_result.data

    question_result = supabase.table("interview_questions").select("*").eq("id", request.question_id).single().execute()

    if not question_result.data:
        raise HTTPException(status_code=404, detail="Question not found")

    question = InterviewQuestion(**question_result.data)

    evaluation = await interview_service.evaluate_answer(
        question=question,
        user_answer=request.user_answer,
        knowledge_context=None
    )

    response_data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "question_id": request.question_id,
        "user_answer": request.user_answer,
        "evaluation_scores": evaluation,
        "feedback": evaluation.get("feedback", ""),
        "strengths": evaluation.get("strengths", []),
        "improvements": evaluation.get("improvements", []),
        "submitted_at": datetime.utcnow().isoformat()
    }

    response_result = supabase.table("interview_responses").insert(response_data).execute()

    if not response_result.data:
        raise HTTPException(status_code=500, detail="Failed to save response")

    completed_questions = session["completed_questions"] + 1
    is_session_complete = completed_questions >= session["total_questions"]

    all_responses = supabase.table("interview_responses").select("evaluation_scores").eq("session_id", session_id).execute()
    scores = [r["evaluation_scores"].get("overall_score", 0) for r in (all_responses.data or []) if r.get("evaluation_scores")]
    avg_score = sum(scores) / len(scores) if scores else None

    update_data = {
        "completed_questions": completed_questions,
        "avg_score": avg_score
    }

    if is_session_complete:
        update_data["status"] = "completed"
        update_data["completed_at"] = datetime.utcnow().isoformat()

        supabase.rpc("update_interview_analytics", {
            "p_user_id": current_user.id,
            "p_domain": session["domain"]
        }).execute()

    supabase.table("interview_sessions").update(update_data).eq("id", session_id).execute()

    next_question = None
    if not is_session_complete:
        try:
            next_q_result = await get_next_question(session_id, current_user)
            next_question = next_q_result.question
        except:
            pass

    return EvaluationResult(
        response=InterviewResponse(**response_result.data[0]),
        question=question,
        is_session_complete=is_session_complete,
        next_question=next_question
    )


@router.get("/sessions/history", response_model=SessionHistory)
async def get_session_history(
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """Get user's interview session history."""
    supabase = get_supabase()

    result = supabase.table("interview_sessions").select("*").eq("user_id", current_user.id).order("started_at", desc=True).limit(limit).execute()

    sessions = [InterviewSession(**s) for s in (result.data or [])]
    avg_performance = sum(s.avg_score for s in sessions if s.avg_score) / len([s for s in sessions if s.avg_score]) if sessions else None

    return SessionHistory(
        sessions=sessions,
        total_sessions=len(sessions),
        avg_performance=avg_performance
    )


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific session."""
    supabase = get_supabase()

    session_result = supabase.table("interview_sessions").select("*").eq("id", session_id).eq("user_id", current_user.id).single().execute()

    if not session_result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    responses_result = supabase.table("interview_responses").select("*").eq("session_id", session_id).execute()

    responses = [InterviewResponse(**r) for r in (responses_result.data or [])]
    question_ids = [r.question_id for r in responses]

    questions = []
    if question_ids:
        questions_result = supabase.table("interview_questions").select("*").in_("id", question_ids).execute()
        questions = [InterviewQuestion(**q) for q in (questions_result.data or [])]

    return SessionDetail(
        session=InterviewSession(**session_result.data),
        responses=responses,
        questions=questions
    )


@router.get("/analytics", response_model=List[PerformanceAnalytics])
async def get_performance_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get performance analytics across all domains."""
    supabase = get_supabase()

    result = supabase.table("interview_performance_analytics").select("*").eq("user_id", current_user.id).execute()

    if not result.data:
        return []

    return [PerformanceAnalytics(**a) for a in result.data]


@router.get("/questions", response_model=List[InterviewQuestion])
async def get_questions(
    role_type: Optional[str] = None,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 20
):
    """Browse available interview questions."""
    supabase = get_supabase()

    query = supabase.table("interview_questions").select("*").eq("is_active", True)

    if role_type:
        query = query.in_("role_type", [role_type, "Both"])
    if domain:
        query = query.in_("domain", [domain, "General"])
    if difficulty:
        query = query.eq("difficulty", difficulty)

    result = query.limit(limit).execute()

    return [InterviewQuestion(**q) for q in (result.data or [])]


@router.post("/sessions/{session_id}/abandon")
async def abandon_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a session as abandoned."""
    supabase = get_supabase()

    result = supabase.table("interview_sessions").update({
        "status": "abandoned"
    }).eq("id", session_id).eq("user_id", current_user.id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session abandoned"}
