"""
Pydantic models for interview preparation system.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DomainType(str, Enum):
    IT = "IT"
    FINANCE = "Finance"
    GENERAL = "General"


class RoleType(str, Enum):
    IT = "IT"
    FINANCE = "Finance"
    BOTH = "Both"


class QuestionCategory(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    CASE_STUDY = "case_study"
    SITUATIONAL = "situational"
    CODING = "coding"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class KnowledgeBaseEntry(BaseModel):
    id: Optional[str] = None
    domain: DomainType
    category: str
    title: str
    content: str
    chunk_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class InterviewQuestion(BaseModel):
    id: Optional[str] = None
    question_text: str
    role_type: RoleType
    domain: DomainType
    category: QuestionCategory
    difficulty: DifficultyLevel
    ideal_answer: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None


class StartSessionRequest(BaseModel):
    role_type: RoleType
    domain: DomainType
    job_id: Optional[str] = None
    total_questions: int = Field(default=5, ge=1, le=20)


class InterviewSession(BaseModel):
    id: Optional[str] = None
    user_id: str
    role_type: RoleType
    domain: DomainType
    job_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    total_questions: int = 0
    completed_questions: int = 0
    avg_score: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class EvaluationScores(BaseModel):
    overall_score: float = Field(ge=1, le=5)
    relevance_score: float = Field(ge=1, le=5)
    completeness_score: float = Field(ge=1, le=5)
    technical_accuracy_score: float = Field(ge=1, le=5)
    communication_score: float = Field(ge=1, le=5)


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    user_answer: str = Field(min_length=10)


class InterviewResponse(BaseModel):
    id: Optional[str] = None
    session_id: str
    question_id: str
    user_answer: str
    evaluation_scores: Optional[EvaluationScores] = None
    feedback: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    submitted_at: Optional[datetime] = None


class QuestionWithContext(BaseModel):
    question: InterviewQuestion
    question_number: int
    total_questions: int
    session_progress: float


class EvaluationResult(BaseModel):
    response: InterviewResponse
    question: InterviewQuestion
    is_session_complete: bool
    next_question: Optional[InterviewQuestion] = None


class PerformanceAnalytics(BaseModel):
    user_id: str
    domain: DomainType
    total_sessions: int = 0
    total_questions_answered: int = 0
    avg_overall_score: Optional[float] = None
    avg_relevance_score: Optional[float] = None
    avg_completeness_score: Optional[float] = None
    avg_technical_accuracy_score: Optional[float] = None
    avg_communication_score: Optional[float] = None
    weak_categories: List[str] = Field(default_factory=list)
    strong_categories: List[str] = Field(default_factory=list)
    last_practice_date: Optional[datetime] = None


class SessionHistory(BaseModel):
    sessions: List[InterviewSession]
    total_sessions: int
    avg_performance: Optional[float] = None


class SessionDetail(BaseModel):
    session: InterviewSession
    responses: List[InterviewResponse]
    questions: List[InterviewQuestion]
