"""
Games API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import logging

from models.games import (
    Game,
    GameTypeInfo,
    GameSession,
    GameAttempt,
    StartGameSessionRequest,
    SubmitGameAnswerRequest,
    GameResult,
    Leaderboard,
    SkillBadge,
)
from api.auth import get_current_user
from services.games.game_service import game_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/types", response_model=List[dict])
async def get_game_types():
    """Get all available game types."""
    try:
        return await game_service.get_game_types()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get game types: {str(e)}")


@router.get("/", response_model=List[Game])
async def get_games(
    game_type: Optional[str] = None,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None
):
    """Browse available games with optional filters."""
    try:
        return await game_service.get_games(game_type, domain, difficulty)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get games: {str(e)}")


@router.get("/{game_id}", response_model=Game)
async def get_game(game_id: str):
    """Get game details by ID."""
    try:
        game = await game_service.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get game: {str(e)}")


@router.get("/sessions/check/{game_id}")
async def check_existing_sessions(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Check if there are active (unfinished) sessions for a game."""
    try:
        active_sessions = await game_service.get_active_sessions_for_game(
            game_id, 
            current_user["id"]
        )
        return {
            "has_active_sessions": len(active_sessions) > 0,
            "active_sessions": active_sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check sessions: {str(e)}")


@router.post("/sessions/start")
async def start_game_session(
    request: StartGameSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start a new game session. If active sessions exist and force_new is False, returns error with session info."""
    try:
        force_new = request.force_new if hasattr(request, 'force_new') else False
        return await game_service.start_session(
            request.game_id, 
            current_user["id"],
            force_new=force_new
        )
    except ValueError as e:
        error_msg = str(e)
        # Check if this is an active sessions error
        if error_msg.startswith("ACTIVE_SESSIONS_EXIST:"):
            import json
            try:
                sessions_data = json.loads(error_msg.replace("ACTIVE_SESSIONS_EXIST: ", ""))
                raise HTTPException(
                    status_code=409,  # Conflict
                    detail={
                        "message": "Active sessions exist",
                        "active_sessions": sessions_data
                    }
                )
            except Exception as parse_err:
                logger.warning(f"Failed to parse active sessions data: {parse_err}")
                raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=404, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/sessions/{session_id}/submit", response_model=GameAttempt)
async def submit_answer(
    session_id: str,
    request: SubmitGameAnswerRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit answer for a game session."""
    try:
        return await game_service.submit_answer(
            session_id,
            request.answer_data,
            current_user["id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete/abandon a game session."""
    try:
        await game_service.delete_session(session_id, current_user["id"])
        return {"message": "Session deleted successfully"}
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif "access denied" in error_msg.lower() or "denied" in error_msg.lower():
            raise HTTPException(status_code=403, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.post("/sessions/{session_id}/complete", response_model=GameResult)
async def complete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Complete a game session and get final results."""
    try:
        return await game_service.complete_session(session_id, current_user["id"])
    except ValueError as e:
        # ValueError means session not found or access denied
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=403, detail=error_msg)
    except Exception as e:
        import traceback
        logger.error(f"Error completing session {session_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to complete session: {str(e)}")


@router.get("/leaderboard/{game_id}", response_model=Leaderboard)
async def get_leaderboard(game_id: str, limit: int = 100):
    """Get leaderboard for a game."""
    try:
        return await game_service.get_leaderboard(game_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")


@router.get("/badges", response_model=List[SkillBadge])
async def get_user_badges(current_user: dict = Depends(get_current_user)):
    """Get user's earned badges."""
    try:
        return await game_service.get_user_badges(current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get badges: {str(e)}")


@router.get("/sessions/history", response_model=List[dict])
async def get_user_sessions_history(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    game_type: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 50
):
    """Get user's game session history with game details."""
    try:
        return await game_service.get_user_sessions_history(
            current_user["id"],
            status=status,
            game_type=game_type,
            domain=domain,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user's game statistics including skills breakdown by game type and domain."""
    try:
        return await game_service.get_user_stats(current_user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/sessions/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get session details with game information."""
    try:
        from database.postgres_client import get_postgres_client
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Get session
        session_row = await db.fetch_one(
            "SELECT * FROM game_sessions WHERE id = $1 AND user_id = $2",
            session_id, current_user["id"]
        )
        
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_dict = dict(session_row)
        game_id = session_dict["game_id"]
        
        # Get game
        game = await game_service.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # If session has selected questions in result_data, use those instead of game's questions
        result_data = session_dict.get("result_data", {})
        if isinstance(result_data, str):
            import json
            try:
                result_data = json.loads(result_data)
            except:
                result_data = {}
        
        if result_data.get("selected_questions"):
            # Override game's questions with session-specific questions (for coding and multiple_choice)
            if game.game_type in ["coding", "multiple_choice"]:
                game_dict = game.model_dump() if hasattr(game, 'model_dump') else game.dict()
                if "game_content" in game_dict:
                    if not isinstance(game_dict["game_content"], dict):
                        game_dict["game_content"] = {}
                    game_dict["game_content"]["questions"] = result_data["selected_questions"]
                    from models.games import Game
                    game = Game(**game_dict)
        
        # Format session
        if session_dict.get("id"):
            session_dict["id"] = str(session_dict["id"])
        if session_dict.get("user_id"):
            session_dict["user_id"] = str(session_dict["user_id"])
        if session_dict.get("game_id"):
            session_dict["game_id"] = str(session_dict["game_id"])
        if session_dict.get("started_at") and hasattr(session_dict["started_at"], "isoformat"):
            session_dict["started_at"] = session_dict["started_at"].isoformat()
        if session_dict.get("completed_at") and hasattr(session_dict["completed_at"], "isoformat"):
            session_dict["completed_at"] = session_dict["completed_at"].isoformat()
        
        return {
            "session": session_dict,
            "game": game.model_dump() if hasattr(game, 'model_dump') else game.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

