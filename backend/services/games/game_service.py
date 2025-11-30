"""
Game service - manages game library, sessions, and evaluations.
"""
import json
import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from database.postgres_client import PostgresClient, get_postgres_client
from models.games import (
    Game, GameSession, GameAttempt, GameTypeInfo, GameStatus,
    StartGameSessionRequest, SubmitGameAnswerRequest, GameResult,
    LeaderboardEntry, Leaderboard, SkillBadge, UserGameStats
)
from services.games.base_game_handler import BaseGameHandler

logger = logging.getLogger(__name__)

# Import handlers (will be registered when available)
try:
    from services.games.coding_handler import CodingGameHandler
    _CODING_HANDLER_AVAILABLE = True
except ImportError:
    _CODING_HANDLER_AVAILABLE = False
    logger.warning("CodingGameHandler not available")

try:
    from services.games.multiple_choice_handler import MultipleChoiceGameHandler
    _MULTIPLE_CHOICE_HANDLER_AVAILABLE = True
except ImportError:
    _MULTIPLE_CHOICE_HANDLER_AVAILABLE = False
    logger.warning("MultipleChoiceGameHandler not available")


class GameService:
    """Service for managing game library and sessions."""
    
    def __init__(self):
        self.handlers: Dict[str, BaseGameHandler] = {}
        # Register available handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register available game handlers."""
        if _CODING_HANDLER_AVAILABLE:
            self.register_handler("coding", CodingGameHandler())
            logger.info("Registered CodingGameHandler")
        
        if _MULTIPLE_CHOICE_HANDLER_AVAILABLE:
            self.register_handler("multiple_choice", MultipleChoiceGameHandler())
            logger.info("Registered MultipleChoiceGameHandler")
    
    def register_handler(self, game_type: str, handler: BaseGameHandler):
        """Register a game handler for a specific game type."""
        self.handlers[game_type] = handler
        logger.info(f"Registered handler for game type: {game_type}")
    
    async def get_game_types(self) -> List[Dict[str, Any]]:
        """Get all available game types."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        rows = await db.fetch_all(
            "SELECT * FROM game_types WHERE is_active = TRUE ORDER BY name"
        )
        
        return [dict(row) for row in rows]
    
    async def get_games(
        self,
        game_type: Optional[str] = None,
        domain: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Game]:
        """Get games with optional filters."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        conditions = ["is_active = TRUE"]
        params = []
        param_num = 1
        
        if game_type:
            conditions.append(f"game_type = ${param_num}")
            params.append(game_type)
            param_num += 1
        
        if domain:
            conditions.append(f"(domain = ${param_num} OR domain IS NULL)")
            params.append(domain)
            param_num += 1
        
        if difficulty:
            conditions.append(f"(difficulty = ${param_num} OR difficulty IS NULL)")
            params.append(difficulty)
            param_num += 1
        
        query = f"SELECT * FROM games WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"
        
        rows = await db.fetch_all(query, *params)
        
        games = []
        for row in rows:
            game_dict = dict(row)
            if game_dict.get("id"):
                game_dict["id"] = str(game_dict["id"])
            if game_dict.get("created_at") and hasattr(game_dict["created_at"], "isoformat"):
                game_dict["created_at"] = game_dict["created_at"].isoformat()
            if game_dict.get("updated_at") and hasattr(game_dict["updated_at"], "isoformat"):
                game_dict["updated_at"] = game_dict["updated_at"].isoformat()
            # Parse game_content from JSONB if it's a string
            if "game_content" in game_dict and isinstance(game_dict["game_content"], str):
                try:
                    game_dict["game_content"] = json.loads(game_dict["game_content"])
                except (json.JSONDecodeError, TypeError):
                    game_dict["game_content"] = {}
            # Parse tags if it's a string or None
            if "tags" in game_dict and (game_dict["tags"] is None or isinstance(game_dict["tags"], str)):
                if game_dict["tags"] is None:
                    game_dict["tags"] = []
                else:
                    try:
                        # Try to parse as JSON array
                        game_dict["tags"] = json.loads(game_dict["tags"])
                    except (json.JSONDecodeError, TypeError):
                        # If it's a comma-separated string, split it
                        game_dict["tags"] = [tag.strip() for tag in game_dict["tags"].split(",") if tag.strip()]
            games.append(Game(**game_dict))
        
        return games
    
    async def get_game(self, game_id: str) -> Optional[Game]:
        """Get a specific game by ID."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        row = await db.fetch_one(
            "SELECT * FROM games WHERE id = $1 AND is_active = TRUE",
            game_id
        )
        
        if not row:
            return None
        
        game_dict = dict(row)
        if game_dict.get("id"):
            game_dict["id"] = str(game_dict["id"])
        if game_dict.get("created_at") and hasattr(game_dict["created_at"], "isoformat"):
            game_dict["created_at"] = game_dict["created_at"].isoformat()
        if game_dict.get("updated_at") and hasattr(game_dict["updated_at"], "isoformat"):
            game_dict["updated_at"] = game_dict["updated_at"].isoformat()
        # Parse game_content from JSONB if it's a string
        if "game_content" in game_dict and isinstance(game_dict["game_content"], str):
            try:
                game_dict["game_content"] = json.loads(game_dict["game_content"])
            except (json.JSONDecodeError, TypeError):
                game_dict["game_content"] = {}
        # Parse tags if it's a string or None
        if "tags" in game_dict and (game_dict["tags"] is None or isinstance(game_dict["tags"], str)):
            if game_dict["tags"] is None:
                game_dict["tags"] = []
            else:
                try:
                    # Try to parse as JSON array
                    game_dict["tags"] = json.loads(game_dict["tags"])
                except (json.JSONDecodeError, TypeError):
                    # If it's a comma-separated string, split it
                    game_dict["tags"] = [tag.strip() for tag in game_dict["tags"].split(",") if tag.strip()]
        
        return Game(**game_dict)
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete/abandon a game session. Only the owner can delete their own sessions."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        import uuid as uuid_lib
        try:
            session_uuid = uuid_lib.UUID(session_id) if isinstance(session_id, str) else session_id
            user_uuid = uuid_lib.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, TypeError):
            session_uuid = session_id
            user_uuid = user_id
        
        # Verify session exists and belongs to user
        session_row = await db.fetch_one(
            "SELECT id, user_id FROM game_sessions WHERE id = $1",
            session_uuid
        )
        
        if not session_row:
            raise ValueError("Session not found")
        
        # Check ownership
        session_user_id = session_row.get('user_id')
        session_user_id_str = str(session_user_id) if session_user_id else None
        current_user_id_str = str(user_id)
        
        if session_user_id_str != current_user_id_str:
            raise ValueError("Access denied: You can only delete your own sessions")
        
        # Delete the session (cascade will handle related attempts)
        await db.execute(
            "DELETE FROM game_sessions WHERE id = $1",
            session_uuid
        )
        
        logger.info(f"Session {session_id} deleted by user {user_id}")
        return True
    
    async def get_active_sessions_for_game(self, game_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all active (unfinished) sessions for a specific game and user."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        import uuid as uuid_lib
        try:
            user_uuid = uuid_lib.UUID(user_id) if isinstance(user_id, str) else user_id
            game_uuid = uuid_lib.UUID(game_id) if isinstance(game_id, str) else game_id
        except (ValueError, TypeError):
            user_uuid = user_id
            game_uuid = game_id
        
        rows = await db.fetch_all(
            """SELECT id, started_at, score, time_taken_seconds, result_data
               FROM game_sessions
               WHERE game_id = $1 AND user_id = $2 AND status = 'active'
               ORDER BY started_at DESC""",
            game_uuid, user_uuid
        )
        
        sessions = []
        for row in rows:
            session_dict = dict(row)
            # Convert UUID to string
            if session_dict.get("id"):
                session_dict["id"] = str(session_dict["id"])
            # Format datetime
            if session_dict.get("started_at") and hasattr(session_dict["started_at"], "isoformat"):
                session_dict["started_at"] = session_dict["started_at"].isoformat()
            # Parse result_data if it's a string
            if isinstance(session_dict.get("result_data"), str):
                try:
                    session_dict["result_data"] = json.loads(session_dict["result_data"])
                except:
                    session_dict["result_data"] = {}
            
            sessions.append(session_dict)
        
        return sessions
    
    async def start_session(self, game_id: str, user_id: str, force_new: bool = False) -> GameSession:
        """Start a new game session. For coding games, randomly selects questions from database.
        
        Args:
            game_id: ID of the game to start
            user_id: ID of the user starting the session
            force_new: If True, creates a new session even if active sessions exist
        """
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Verify game exists
        game = await self.get_game(game_id)
        if not game:
            raise ValueError(f"Game not found: {game_id}")
        
        # Check for existing active sessions unless force_new is True
        if not force_new:
            active_sessions = await self.get_active_sessions_for_game(game_id, user_id)
            if active_sessions:
                # Return information about existing sessions instead of creating new one
                raise ValueError(f"ACTIVE_SESSIONS_EXIST: {json.dumps(active_sessions)}")
        
        session_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        
        logger.info(f"Starting session {session_id} for user {user_id} (type: {type(user_id)})")
        
        # Convert user_id and game_id to UUID if they're strings (for proper database storage)
        import uuid as uuid_lib
        try:
            user_uuid = uuid_lib.UUID(user_id) if isinstance(user_id, str) else user_id
            game_uuid = uuid_lib.UUID(game_id) if isinstance(game_id, str) else game_id
            session_uuid = uuid_lib.UUID(session_id)
            logger.info(f"Converted user_id to UUID: {user_uuid}")
        except (ValueError, TypeError) as e:
            # If UUID conversion fails, use as-is
            logger.warning(f"UUID conversion failed: {e}, using original values")
            user_uuid = user_id
            game_uuid = game_id
            session_uuid = session_id
        
        # For coding games, select random questions from database at session start
        session_questions = None
        if game.game_type == "coding" and game.game_content.get("language"):
            try:
                from services.games.question_database import question_database
                
                language = game.game_content.get("language")
                difficulty = game.difficulty or "beginner"
                
                # Get random questions from database
                db_questions = await question_database.get_random_questions(
                    language=language,
                    difficulty=difficulty,
                    num_questions=5  # Default to 5 questions per session
                )
                
                if db_questions and len(db_questions) > 0:
                    # Transform database questions to game format
                    session_questions = []
                    for db_q in db_questions:
                        session_questions.append({
                            "description": db_q["description"],
                            "function_signature": db_q.get("function_signature"),
                            "starter_code": db_q["starter_code"],
                            "test_cases": db_q["test_cases"],
                            "concept": db_q["concept"],
                            "question_number": len(session_questions) + 1,
                            "hints": db_q.get("hints", [])
                        })
                    
                    logger.info(f"Selected {len(session_questions)} random questions from database for session")
                    
                    # Increment usage count for selected questions
                    for db_q in db_questions:
                        question_id = db_q.get("id")
                        if question_id:
                            # Convert UUID to string if needed
                            if hasattr(question_id, '__str__'):
                                question_id = str(question_id)
                            try:
                                await question_database.increment_usage(question_id)
                            except Exception as e:
                                logger.warning(f"Failed to increment usage for question {question_id}: {e}")
                else:
                    # Fall back to questions already in game_content if database has none
                    logger.warning(f"No questions found in database for {language} {difficulty}, using game's default questions")
            except Exception as e:
                logger.warning(f"Error selecting questions from database: {e}, using game's default questions")
        
        # For multiple choice games, select random questions from database at session start
        if game.game_type == "multiple_choice":
            try:
                from services.games.multiple_choice_question_database import multiple_choice_question_database
                
                # Get game configuration for filtering
                topic = game.game_content.get("topic")
                category = game.game_content.get("category", "general")
                difficulty = game.difficulty or "beginner"
                domain = game.domain
                
                # Get number of questions from game config
                questions_per_session = game.game_content.get("questions_per_session", 10)
                
                # Get random questions from database
                db_questions = await multiple_choice_question_database.get_random_questions(
                    topic=topic,
                    category=category,
                    difficulty=difficulty,
                    domain=domain,
                    num_questions=questions_per_session
                )
                
                if db_questions and len(db_questions) > 0:
                    # Transform database questions to game format
                    import random
                    session_questions = []
                    for db_q in db_questions:
                        # Shuffle options to randomize answer order for each session
                        options = list(db_q["options"]) if isinstance(db_q["options"], list) else []
                        original_correct_id = str(db_q["correct_answer"]).lower()
                        
                        # Find the correct option by matching the original correct_answer ID
                        correct_option_text = None
                        for opt in options:
                            if isinstance(opt, dict) and str(opt.get("id", "")).lower() == original_correct_id:
                                correct_option_text = opt.get("text")
                                break
                        
                        # Shuffle the options array
                        random.shuffle(options)
                        
                        # Reassign sequential IDs (a, b, c, d...) to shuffled options
                        new_correct_id = None
                        for i, opt in enumerate(options):
                            if isinstance(opt, dict):
                                # Assign new sequential ID
                                new_id = chr(97 + i)  # 'a', 'b', 'c', 'd'...
                                opt["id"] = new_id
                                
                                # If this is the correct option (match by text), save its new ID
                                if correct_option_text and opt.get("text") == correct_option_text:
                                    new_correct_id = new_id
                        
                        # Fallback: if we couldn't find the correct option, use the first one
                        if not new_correct_id and options:
                            new_correct_id = options[0].get("id", "a") if isinstance(options[0], dict) else "a"
                        
                        session_questions.append({
                            "question_text": db_q["question_text"],
                            "options": options,
                            "correct_answer": new_correct_id or original_correct_id,
                            "explanation": db_q.get("explanation"),
                            "question_number": len(session_questions) + 1,
                            "points": db_q.get("points", 10)
                        })
                    
                    logger.info(f"Selected {len(session_questions)} random MC questions from database for session")
                    
                    # Increment usage count for selected questions
                    for db_q in db_questions:
                        question_id = db_q.get("id")
                        if question_id:
                            if hasattr(question_id, '__str__'):
                                question_id = str(question_id)
                            try:
                                await multiple_choice_question_database.increment_usage(question_id)
                            except Exception as e:
                                logger.warning(f"Failed to increment usage for MC question {question_id}: {e}")
                else:
                    # Fall back to questions already in game_content if database has none
                    logger.warning(f"No MC questions found in database for {category} {difficulty}, using game's default questions")
            except Exception as e:
                logger.warning(f"Error selecting MC questions from database: {e}, using game's default questions")
        
        # Store selected questions in result_data if we have them
        result_data = {}
        if session_questions:
            result_data["selected_questions"] = session_questions
        
        await db.execute(
            """INSERT INTO game_sessions 
               (id, user_id, game_id, status, started_at, result_data)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb)""",
            session_uuid, user_uuid, game_uuid, "active", started_at, json.dumps(result_data)
        )
        
        logger.info(f"Session created successfully with user_id stored as: {user_uuid}")
        
        return GameSession(
            id=str(session_uuid),
            user_id=str(user_uuid),
            game_id=str(game_uuid),
            status=GameStatus.ACTIVE,
            started_at=started_at
        )
    
    async def submit_answer(
        self,
        session_id: str,
        answer_data: Dict[str, Any],
        user_id: str
    ) -> GameAttempt:
        """Submit an answer for a game session."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Get session - compare user IDs as strings to avoid UUID comparison issues
        logger.info(f"Submitting answer for session {session_id}, user {user_id}")
        
        # First check if session exists and belongs to user
        session_check = await db.fetch_one(
            "SELECT id, user_id, status FROM game_sessions WHERE id = $1",
            session_id
        )
        
        if not session_check:
            logger.warning(f"Session {session_id} not found")
            raise ValueError("Session not found")
        
        # Compare user IDs as strings
        session_user_id = session_check.get('user_id')
        session_user_id_str = str(session_user_id) if session_user_id else None
        current_user_id_str = str(user_id)
        
        if session_user_id_str != current_user_id_str:
            logger.warning(f"Access denied: Session belongs to {session_user_id_str}, but user is {current_user_id_str}")
            raise ValueError("Session not found")
        
        # Get full session
        session_row = await db.fetch_one(
            "SELECT * FROM game_sessions WHERE id = $1",
            session_id
        )
        
        session_dict = dict(session_row)
        if session_dict["status"] != "active":
            raise ValueError("Session is not active")
        
        # Convert session_id to string early (might be UUID object from database)
        import uuid as uuid_lib
        if isinstance(session_id, uuid_lib.UUID):
            session_id_str = str(session_id)
        else:
            session_id_str = str(session_id) if session_id else None
        
        # Get game
        game_id_from_session = str(session_dict["game_id"]) if session_dict.get("game_id") else None
        game = await self.get_game(game_id_from_session) if game_id_from_session else None
        if not game:
            raise ValueError("Game not found")
        
        # For games with session-specific questions (coding, multiple_choice), inject selected questions
        # from session.result_data into game.game_content
        if game.game_type in ["coding", "multiple_choice"]:
            result_data = session_dict.get("result_data", {})
            if isinstance(result_data, str):
                try:
                    result_data = json.loads(result_data)
                except (json.JSONDecodeError, TypeError):
                    result_data = {}
            
            if result_data.get("selected_questions"):
                # Override game's questions with session-specific questions
                game_dict = game.model_dump() if hasattr(game, 'model_dump') else game.dict()
                if "game_content" in game_dict:
                    if not isinstance(game_dict["game_content"], dict):
                        game_dict["game_content"] = {}
                    game_dict["game_content"]["questions"] = result_data["selected_questions"]
                    from models.games import Game
                    game = Game(**game_dict)
        
        # Ensure game.id is a string (get_game should convert it, but double-check)
        if isinstance(game.id, uuid_lib.UUID):
            game_id_str = str(game.id)
        else:
            game_id_str = str(game.id) if game.id else None
        
        # Create attempt
        attempt_id = str(uuid.uuid4())
        submitted_at = datetime.now(timezone.utc)
        
        # Convert IDs to UUID for database
        try:
            attempt_uuid = uuid_lib.UUID(attempt_id)
            game_uuid = uuid_lib.UUID(game_id_str) if game_id_str else None
        except (ValueError, TypeError):
            attempt_uuid = attempt_id
            game_uuid = game_id_str
        
        # Ensure answer_data is a dict (not a JSON string)
        if isinstance(answer_data, str):
            try:
                answer_data = json.loads(answer_data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse answer_data as JSON: {answer_data}")
                answer_data = {}
        
        if game.game_type in self.handlers:
            handler = self.handlers[game.game_type]
            attempt_obj = GameAttempt(
                session_id=session_id_str,
                game_id=game_id_str,
                answer_data=answer_data
            )
            evaluation_result = await handler.evaluate_attempt(game, attempt_obj)
            points_earned = handler.calculate_score(evaluation_result)
            is_correct = evaluation_result.get("passed", evaluation_result.get("is_correct", False))
        else:
            # Default evaluation if no handler
            logger.warning(f"No handler registered for game type: {game.game_type}")
            evaluation_result = {"status": "pending", "message": "Handler not implemented yet"}
        
        # Convert session_id to UUID for database
        try:
            session_uuid = uuid_lib.UUID(session_id) if isinstance(session_id, str) else session_id
        except (ValueError, TypeError):
            session_uuid = session_id
        
        # Save attempt
        await db.execute(
            """INSERT INTO game_attempts 
               (id, session_id, game_id, answer_data, evaluation_result, is_correct, points_earned, submitted_at)
               VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8)""",
            attempt_uuid, session_uuid, game_uuid, json.dumps(answer_data),
            json.dumps(evaluation_result) if evaluation_result else None,
            is_correct, points_earned, submitted_at
        )
        
        return GameAttempt(
            id=attempt_id,
            session_id=session_id_str,
            game_id=game_id_str,
            answer_data=answer_data,
            evaluation_result=evaluation_result,
            is_correct=is_correct,
            points_earned=points_earned,
            submitted_at=submitted_at
        )
    
    async def complete_session(self, session_id: str, user_id: str) -> GameResult:
        """Complete a game session and calculate final results."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Get session - check if it exists and belongs to user
        # Allow completing even if already completed (to get results again)
        # First, let's check what the session actually has
        logger.info(f"Attempting to complete session {session_id} for user {user_id}")
        logger.info(f"User ID type: {type(user_id)}, value: {user_id}")
        
        # Try to find the session first (without user_id check)
        session_check = await db.fetch_one(
            "SELECT id, user_id, status FROM game_sessions WHERE id = $1",
            session_id
        )
        
        if not session_check:
            logger.warning(f"Session {session_id} not found in database")
            raise ValueError(f"Session not found: {session_id}")
        
        session_user_id = session_check['user_id']
        logger.info(f"Session found - stored user_id: {session_user_id} (type: {type(session_user_id)})")
        logger.info(f"Current user_id: {user_id} (type: {type(user_id)})")
        
        # Convert both to strings for comparison (handle UUID objects, strings, etc.)
        import uuid as uuid_lib
        try:
            # Try to normalize both to UUID strings
            if isinstance(session_user_id, uuid_lib.UUID):
                session_user_str = str(session_user_id)
            elif isinstance(session_user_id, str):
                # If it's a string, try to parse as UUID to normalize format
                try:
                    session_user_str = str(uuid_lib.UUID(session_user_id))
                except (ValueError, TypeError):
                    session_user_str = session_user_id
            else:
                session_user_str = str(session_user_id) if session_user_id else None
            
            if isinstance(user_id, uuid_lib.UUID):
                current_user_str = str(user_id)
            elif isinstance(user_id, str):
                try:
                    current_user_str = str(uuid_lib.UUID(user_id))
                except (ValueError, TypeError):
                    current_user_str = user_id
            else:
                current_user_str = str(user_id) if user_id else None
        except Exception as e:
            logger.error(f"Error normalizing user IDs: {e}")
            # Fallback to simple string conversion
            session_user_str = str(session_user_id) if session_user_id else None
            current_user_str = str(user_id) if user_id else None
        
        logger.info(f"Normalized comparison: session_user='{session_user_str}' vs current_user='{current_user_str}'")
        logger.info(f"Match: {session_user_str == current_user_str}")
        
        if session_user_str != current_user_str:
            logger.warning(f"Access denied: Session {session_id} belongs to user '{session_user_str}', but current user is '{current_user_str}'")
            logger.warning(f"Raw values - session: {repr(session_user_id)}, current: {repr(user_id)}")
            raise ValueError("Session not found or access denied")
        
        # Now get the full session
        session_row = await db.fetch_one(
            "SELECT * FROM game_sessions WHERE id = $1",
            session_id
        )
        
        session_dict = dict(session_row)
        game_id = session_dict["game_id"]
        
        # Get all attempts
        attempt_rows = await db.fetch_all(
            "SELECT * FROM game_attempts WHERE session_id = $1 ORDER BY submitted_at",
            session_id
        )
        
        attempts = []
        total_score = 0
        
        for row in attempt_rows:
            attempt_dict = dict(row)
            if attempt_dict.get("id"):
                attempt_dict["id"] = str(attempt_dict["id"])
            
            # Convert UUIDs to strings for Pydantic validation
            if attempt_dict.get("session_id"):
                attempt_dict["session_id"] = str(attempt_dict["session_id"])
            if attempt_dict.get("game_id"):
                attempt_dict["game_id"] = str(attempt_dict["game_id"])
            
            # Parse answer_data if it's a string
            if attempt_dict.get("answer_data"):
                if isinstance(attempt_dict["answer_data"], str):
                    try:
                        attempt_dict["answer_data"] = json.loads(attempt_dict["answer_data"])
                    except:
                        pass # Keep as string if parse fails, Pydantic will catch it
            else:
                # Ensure answer_data is at least an empty dict if None
                attempt_dict["answer_data"] = {}

            if attempt_dict.get("evaluation_result"):
                if isinstance(attempt_dict["evaluation_result"], str):
                    try:
                        attempt_dict["evaluation_result"] = json.loads(attempt_dict["evaluation_result"])
                    except:
                        attempt_dict["evaluation_result"] = {}
            if attempt_dict.get("submitted_at") and hasattr(attempt_dict["submitted_at"], "isoformat"):
                attempt_dict["submitted_at"] = attempt_dict["submitted_at"].isoformat()
            
            attempts.append(GameAttempt(**attempt_dict))
            total_score += attempt_dict.get("points_earned", 0)
        
        # Calculate time taken
        started_at = session_dict["started_at"]
        completed_at = datetime.now(timezone.utc)
        time_taken = int((completed_at - started_at).total_seconds())
        
        # Update session
        await db.execute(
            """UPDATE game_sessions 
               SET status = $1, score = $2, time_taken_seconds = $3, completed_at = $4, result_data = $5::jsonb
               WHERE id = $6""",
            "completed", total_score, time_taken, completed_at,
            json.dumps({"final_score": total_score, "attempts_count": len(attempts)}),
            session_id
        )
        
        # Update leaderboard - convert game_id to UUID if needed
        import uuid as uuid_lib
        try:
            game_uuid = uuid_lib.UUID(str(game_id)) if isinstance(game_id, str) else game_id
        except (ValueError, TypeError):
            game_uuid = game_id
        
        await self._update_leaderboard(str(game_uuid), str(user_id), str(session_id), total_score, time_taken, completed_at)
        
        # Update user stats
        game = await self.get_game(game_id)
        if game:
            await self._update_user_stats(user_id, game.game_type, total_score)
        
        # Get leaderboard position
        leaderboard_position = await self._get_leaderboard_position(game_id, user_id)
        
        # Check for badges (can be implemented later)
        badges_earned = []
        
        # Build session object
        session_dict["id"] = str(session_dict["id"])
        if session_dict.get("user_id"):
            session_dict["user_id"] = str(session_dict["user_id"])
        if session_dict.get("game_id"):
            session_dict["game_id"] = str(session_dict["game_id"])
        
        session_dict["status"] = "completed"
        session_dict["score"] = total_score
        session_dict["time_taken_seconds"] = time_taken
        session_dict["result_data"] = {"final_score": total_score, "attempts_count": len(attempts)}
        
        if session_dict.get("started_at") and hasattr(session_dict["started_at"], "isoformat"):
            session_dict["started_at"] = session_dict["started_at"].isoformat()
        session_dict["completed_at"] = completed_at.isoformat()
        
        session = GameSession(**session_dict)
        
        return GameResult(
            session=session,
            attempts=attempts,
            final_score=total_score,
            badges_earned=badges_earned,
            leaderboard_position=leaderboard_position
        )
    
    async def _update_leaderboard(
        self,
        game_id: str,
        user_id: str,
        session_id: str,
        score: int,
        time_taken: int,
        completed_at: datetime
    ):
        """Update leaderboard for a game."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Check if user already has an entry
        existing = await db.fetch_one(
            "SELECT * FROM game_leaderboards WHERE game_id = $1 AND user_id = $2",
            game_id, user_id
        )
        
        if existing:
            # Update if score is better
            if score > existing["score"] or (score == existing["score"] and time_taken < existing["time_taken_seconds"]):
                await db.execute(
                    """UPDATE game_leaderboards 
                       SET session_id = $1, score = $2, time_taken_seconds = $3, completed_at = $4
                       WHERE game_id = $5 AND user_id = $6""",
                    session_id, score, time_taken, completed_at, game_id, user_id
                )
        else:
            # Insert new entry
            await db.execute(
                """INSERT INTO game_leaderboards 
                   (game_id, user_id, session_id, score, time_taken_seconds, completed_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                game_id, user_id, session_id, score, time_taken, completed_at
            )
        
        # Recalculate ranks
        await self._recalculate_ranks(game_id)
    
    async def _recalculate_ranks(self, game_id: str):
        """Recalculate ranks for a game leaderboard."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Get all entries ordered by score desc, time asc
        entries = await db.fetch_all(
            """SELECT id FROM game_leaderboards 
               WHERE game_id = $1 
               ORDER BY score DESC, time_taken_seconds ASC""",
            game_id
        )
        
        # Update ranks
        for rank, entry in enumerate(entries, start=1):
            await db.execute(
                "UPDATE game_leaderboards SET rank = $1 WHERE id = $2",
                rank, entry["id"]
            )
    
    async def _get_leaderboard_position(self, game_id: str, user_id: str) -> Optional[int]:
        """Get user's position on leaderboard."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        row = await db.fetch_one(
            "SELECT rank FROM game_leaderboards WHERE game_id = $1 AND user_id = $2",
            game_id, user_id
        )
        
        return row["rank"] if row else None
    
    async def _update_user_stats(self, user_id: str, game_type: str, score: int):
        """Update user statistics for a game type."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Get or create stats
        stats_row = await db.fetch_one(
            "SELECT * FROM user_game_stats WHERE user_id = $1 AND game_type = $2",
            user_id, game_type
        )
        
        if stats_row:
            stats = dict(stats_row)
            total_played = stats["total_games_played"] + 1
            total_score = stats["total_score"] + score
            avg_score = total_score / total_played
            best_score = max(stats["best_score"] or 0, score)
            completed = stats["games_completed"] + 1
            
            await db.execute(
                """UPDATE user_game_stats 
                   SET total_games_played = $1, total_score = $2, avg_score = $3, 
                       best_score = $4, games_completed = $5, last_played_at = $6, updated_at = $7
                   WHERE user_id = $8 AND game_type = $9""",
                total_played, total_score, avg_score, best_score, completed,
                datetime.now(timezone.utc), datetime.now(timezone.utc), user_id, game_type
            )
        else:
            await db.execute(
                """INSERT INTO user_game_stats 
                   (user_id, game_type, total_games_played, total_score, avg_score, 
                    best_score, games_completed, last_played_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                user_id, game_type, 1, score, float(score), score, 1,
                datetime.now(timezone.utc), datetime.now(timezone.utc)
            )
    
    async def get_leaderboard(self, game_id: str, limit: int = 100) -> Leaderboard:
        """Get leaderboard for a game."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Get game title
        game = await self.get_game(game_id)
        game_title = game.title if game else "Unknown Game"
        
        # Get leaderboard entries
        rows = await db.fetch_all(
            """SELECT lb.*, u.username 
               FROM game_leaderboards lb
               LEFT JOIN users u ON lb.user_id = u.id
               WHERE lb.game_id = $1 
               ORDER BY lb.rank ASC
               LIMIT $2""",
            game_id, limit
        )
        
        entries = []
        for row in rows:
            entry_dict = dict(row)
            if entry_dict.get("user_id"):
                entry_dict["user_id"] = str(entry_dict["user_id"])
            if entry_dict.get("completed_at") and hasattr(entry_dict["completed_at"], "isoformat"):
                entry_dict["completed_at"] = entry_dict["completed_at"].isoformat()
            entries.append(LeaderboardEntry(**entry_dict))
        
        # Get total players
        total_row = await db.fetch_one(
            "SELECT COUNT(*) as count FROM game_leaderboards WHERE game_id = $1",
            game_id
        )
        total_players = total_row["count"] if total_row else 0
        
        return Leaderboard(
            game_id=game_id,
            game_title=game_title,
            entries=entries,
            total_players=total_players
        )
    
    async def get_user_badges(self, user_id: str) -> List[SkillBadge]:
        """Get user's earned badges."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        rows = await db.fetch_all(
            "SELECT * FROM skill_badges WHERE user_id = $1 ORDER BY earned_at DESC",
            user_id
        )
        
        badges = []
        for row in rows:
            badge_dict = dict(row)
            if badge_dict.get("id"):
                badge_dict["id"] = str(badge_dict["id"])
            if badge_dict.get("user_id"):
                badge_dict["user_id"] = str(badge_dict["user_id"])
            if badge_dict.get("game_id"):
                badge_dict["game_id"] = str(badge_dict["game_id"])
            if badge_dict.get("earned_at") and hasattr(badge_dict["earned_at"], "isoformat"):
                badge_dict["earned_at"] = badge_dict["earned_at"].isoformat()
            badges.append(SkillBadge(**badge_dict))
        
        return badges
    
    async def get_user_sessions_history(
        self,
        user_id: str,
        status: Optional[str] = None,
        game_type: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's game session history with game details."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        conditions = ["gs.user_id = $1"]
        params = [user_id]
        param_num = 2
        
        if status:
            conditions.append(f"gs.status = ${param_num}")
            params.append(status)
            param_num += 1
        
        if game_type:
            conditions.append(f"g.game_type = ${param_num}")
            params.append(game_type)
            param_num += 1
        
        if domain:
            conditions.append(f"g.domain = ${param_num}")
            params.append(domain)
            param_num += 1
        
        query = f"""
            SELECT 
                gs.id, gs.user_id, gs.game_id, gs.status, gs.score, 
                gs.time_taken_seconds, gs.started_at, gs.completed_at, gs.result_data,
                g.title, g.game_type, g.domain, g.difficulty, g.points
            FROM game_sessions gs
            JOIN games g ON gs.game_id = g.id
            WHERE {' AND '.join(conditions)}
            ORDER BY gs.started_at DESC
            LIMIT ${param_num}
        """
        params.append(limit)
        
        rows = await db.fetch_all(query, *params)
        
        sessions = []
        for row in rows:
            session_dict = dict(row)
            # Convert UUIDs to strings
            if session_dict.get("id"):
                session_dict["id"] = str(session_dict["id"])
            if session_dict.get("user_id"):
                session_dict["user_id"] = str(session_dict["user_id"])
            if session_dict.get("game_id"):
                session_dict["game_id"] = str(session_dict["game_id"])
            # Convert datetimes
            if session_dict.get("started_at") and hasattr(session_dict["started_at"], "isoformat"):
                session_dict["started_at"] = session_dict["started_at"].isoformat()
            if session_dict.get("completed_at") and hasattr(session_dict["completed_at"], "isoformat"):
                session_dict["completed_at"] = session_dict["completed_at"].isoformat()
            # Parse JSONB fields
            if isinstance(session_dict.get("result_data"), str):
                try:
                    session_dict["result_data"] = json.loads(session_dict["result_data"])
                except:
                    session_dict["result_data"] = {}
            sessions.append(session_dict)
        
        return sessions
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's game statistics across all game types and domains."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        # Get stats by game type
        rows = await db.fetch_all(
            "SELECT * FROM user_game_stats WHERE user_id = $1",
            user_id
        )
        
        stats_by_type = {}
        total_games = 0
        total_score = 0
        total_badges = 0
        
        for row in rows:
            stats_dict = dict(row)
            if stats_dict.get("user_id"):
                stats_dict["user_id"] = str(stats_dict["user_id"])
            if stats_dict.get("last_played_at") and hasattr(stats_dict["last_played_at"], "isoformat"):
                stats_dict["last_played_at"] = stats_dict["last_played_at"].isoformat()
            
            game_type = stats_dict["game_type"]
            stats_by_type[game_type] = UserGameStats(**stats_dict)
            
            total_games += stats_dict["total_games_played"]
            total_score += stats_dict["total_score"]
            total_badges += stats_dict["badges_earned"]
        
        # Get stats by domain
        domain_rows = await db.fetch_all(
            """
            SELECT 
                g.domain,
                COUNT(*) as total_challenges,
                COUNT(CASE WHEN gs.status = 'completed' THEN 1 END) as completed_challenges,
                COALESCE(SUM(CASE WHEN gs.status = 'completed' THEN gs.score ELSE 0 END), 0) as total_score,
                COALESCE(AVG(CASE WHEN gs.status = 'completed' THEN gs.score ELSE NULL END), 0) as avg_score,
                COALESCE(MAX(CASE WHEN gs.status = 'completed' THEN gs.score ELSE 0 END), 0) as best_score
            FROM game_sessions gs
            JOIN games g ON gs.game_id = g.id
            WHERE gs.user_id = $1 AND g.domain IS NOT NULL
            GROUP BY g.domain
            """,
            user_id
        )
        
        stats_by_domain = {}
        for row in domain_rows:
            domain_dict = dict(row)
            domain = domain_dict["domain"]
            stats_by_domain[domain] = {
                "domain": domain,
                "total_challenges": domain_dict["total_challenges"],
                "completed_challenges": domain_dict["completed_challenges"],
                "total_score": int(domain_dict["total_score"] or 0),
                "avg_score": float(domain_dict["avg_score"] or 0),
                "best_score": int(domain_dict["best_score"] or 0)
            }
        
        return {
            "stats_by_type": stats_by_type,
            "stats_by_domain": stats_by_domain,
            "total_games_played": total_games,
            "total_score": total_score,
            "total_badges": total_badges,
            "badges": await self.get_user_badges(user_id)
        }


# Singleton instance
game_service = GameService()

