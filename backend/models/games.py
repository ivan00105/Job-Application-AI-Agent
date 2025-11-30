"""
Pydantic models for game library system.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class GameType(str, Enum):
    CODING = "coding"
    MULTIPLE_CHOICE = "multiple_choice"
    PERSONALITY = "personality"
    PUZZLE = "puzzle"
    SYSTEM_DESIGN = "system_design"
    CASE_STUDY = "case_study"


class GameStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DomainType(str, Enum):
    IT = "IT"
    FINANCE = "Finance"
    GENERAL = "General"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# Base game model
class Game(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    game_type: str
    domain: Optional[str] = None
    difficulty: Optional[str] = None
    game_content: Dict[str, Any] = Field(default_factory=dict)
    time_limit_minutes: Optional[int] = None
    points: int = 100
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GameTypeInfo(BaseModel):
    id: Optional[str] = None
    type_code: str
    name: str
    description: Optional[str] = None
    handler_class: Optional[str] = None
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None


# Game session
class GameSession(BaseModel):
    id: Optional[str] = None
    user_id: str
    game_id: str
    status: GameStatus = GameStatus.ACTIVE
    score: Optional[int] = None
    time_taken_seconds: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_data: Dict[str, Any] = Field(default_factory=dict)


# Game attempt
class GameAttempt(BaseModel):
    id: Optional[str] = None
    session_id: str
    game_id: str
    answer_data: Dict[str, Any]
    evaluation_result: Optional[Dict[str, Any]] = None
    is_correct: Optional[bool] = None
    points_earned: Optional[int] = None
    submitted_at: Optional[datetime] = None


# Request/Response models
class StartGameSessionRequest(BaseModel):
    game_id: str
    force_new: bool = False  # If True, creates new session even if active sessions exist


class SubmitGameAnswerRequest(BaseModel):
    session_id: str
    answer_data: Dict[str, Any]


class GameResult(BaseModel):
    session: GameSession
    attempts: List[GameAttempt] = Field(default_factory=list)
    final_score: int
    badges_earned: List[str] = Field(default_factory=list)
    leaderboard_position: Optional[int] = None


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: Optional[str] = None
    score: int
    time_taken_seconds: Optional[int] = None
    completed_at: datetime


class Leaderboard(BaseModel):
    game_id: str
    game_title: str
    entries: List[LeaderboardEntry]
    total_players: int


class SkillBadge(BaseModel):
    id: Optional[str] = None
    user_id: str
    badge_type: str
    game_id: Optional[str] = None
    game_type: Optional[str] = None
    earned_at: Optional[datetime] = None
    verified: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserGameStats(BaseModel):
    user_id: str
    game_type: str
    total_games_played: int = 0
    total_score: int = 0
    avg_score: Optional[float] = None
    best_score: Optional[int] = None
    games_completed: int = 0
    badges_earned: int = 0
    last_played_at: Optional[datetime] = None

