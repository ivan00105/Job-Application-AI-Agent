"""
Handler for multiple choice quiz games.
"""
import logging
from typing import Dict, Any

from services.games.base_game_handler import BaseGameHandler
from models.games import Game, GameAttempt

logger = logging.getLogger(__name__)


class MultipleChoiceGameHandler(BaseGameHandler):
    """Handler for multiple choice quiz games."""
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Validate multiple choice game content structure.
        
        Supports two formats:
        1. Single question (legacy):
        {
            "question": "Question text",
            "options": [{"id": "a", "text": "Option A"}, ...],
            "correct_answer": "a"
        }
        
        2. Multiple questions (new):
        {
            "questions": [
                {
                    "question_text": "Question text",
                    "options": [{"id": "a", "text": "Option A"}, ...],
                    "correct_answer": "a",
                    "explanation": "Why this is correct"
                }
            ]
        }
        """
        # Check if it's the new multi-question format
        if "questions" in content:
            if not isinstance(content["questions"], list) or len(content["questions"]) == 0:
                logger.warning("questions must be a non-empty list")
                return False
            
            # Validate each question
            for i, question in enumerate(content["questions"]):
                if not isinstance(question, dict):
                    logger.warning(f"Question {i} must be a dictionary")
                    return False
                
                required = ["question_text", "options", "correct_answer"]
                for field in required:
                    if field not in question:
                        logger.warning(f"Question {i} missing required field: {field}")
                        return False
                
                if not isinstance(question["options"], list) or len(question["options"]) < 2:
                    logger.warning(f"Question {i} must have at least 2 options")
                    return False
                
                # Validate correct_answer is one of the option IDs
                option_ids = [opt.get("id") for opt in question["options"]]
                if question["correct_answer"] not in option_ids:
                    logger.warning(f"Question {i} correct_answer must be one of the option IDs")
                    return False
            
            return True
        
        # Legacy single question format
        required_fields = ["question", "options", "correct_answer"]
        for field in required_fields:
            if field not in content:
                logger.warning(f"Missing required field: {field}")
                return False
        
        if not isinstance(content["options"], list) or len(content["options"]) < 2:
            logger.warning("options must be a list with at least 2 items")
            return False
        
        return True
    
    async def evaluate_attempt(
        self,
        game: Game,
        attempt: GameAttempt
    ) -> Dict[str, Any]:
        """
        Evaluate user's answer submission.
        
        Supports both single question and multi-question formats.
        
        Args:
            game: The multiple choice game
            attempt: User's answer submission
            
        Returns:
            Evaluation result with correctness and score
        """
        content = game.game_content
        answer_data = attempt.answer_data
        
        selected_answer = answer_data.get("selected_answer", "").strip().lower()
        question_index = answer_data.get("question_index", None)  # For multi-question games
        
        if not selected_answer:
            return {
                "passed": False,
                "error": "No answer selected",
                "is_correct": False,
                "question_index": question_index
            }
        
        # Check if it's multi-question format
        if "questions" in content:
            if question_index is None:
                return {
                    "passed": False,
                    "error": "question_index required for multi-question games",
                    "is_correct": False
                }
            
            questions = content["questions"]
            if question_index < 0 or question_index >= len(questions):
                return {
                    "passed": False,
                    "error": f"Invalid question_index: {question_index}",
                    "is_correct": False
                }
            
            question = questions[question_index]
            
            # Validate question has correct_answer
            if "correct_answer" not in question:
                logger.error(
                    f"Question {question_index} missing correct_answer field. "
                    f"Question keys: {list(question.keys())}, "
                    f"Question content: {question}"
                )
                return {
                    "passed": False,
                    "error": "Question configuration error: missing correct_answer",
                    "is_correct": False,
                    "question_index": question_index
                }
            
            # Log for debugging
            logger.debug(
                f"Evaluating MC answer: question_index={question_index}, "
                f"selected_answer={selected_answer}, "
                f"correct_answer={question.get('correct_answer')}"
            )
            
            correct_answer = str(question["correct_answer"]).strip().lower()
            is_correct = selected_answer == correct_answer
            
            return {
                "passed": is_correct,
                "is_correct": is_correct,
                "selected_answer": selected_answer,
                "correct_answer": correct_answer,
                "explanation": question.get("explanation", ""),
                "question_index": question_index,
                "total_questions": len(questions)
            }
        
        # Legacy single question format
        if "correct_answer" not in content:
            logger.error(f"Game content missing correct_answer field. Content keys: {list(content.keys())}")
            return {
                "passed": False,
                "error": "Game configuration error: missing correct_answer",
                "is_correct": False
            }
        
        correct_answer = str(content["correct_answer"]).strip().lower()
        is_correct = selected_answer == correct_answer
        
        return {
            "passed": is_correct,
            "is_correct": is_correct,
            "selected_answer": selected_answer,
            "correct_answer": correct_answer,
            "explanation": content.get("explanation", "")
        }
    
    def calculate_score(
        self,
        evaluation_result: Dict[str, Any]
    ) -> int:
        """
        Calculate points earned based on evaluation.
        
        Args:
            evaluation_result: Result from evaluate_attempt
            
        Returns:
            Points earned (0 if incorrect, full points if correct)
        """
        if evaluation_result.get("passed", False):
            # For multi-question games, calculate partial score
            if "total_questions" in evaluation_result:
                # Points per question (assuming equal distribution)
                # This will be aggregated across all questions
                return 10  # Default points per question
            return 100  # Full points for single question
        return 0

