"""
Handler for coding/algorithm challenges.
"""
import logging
from typing import Dict, Any

from services.games.base_game_handler import BaseGameHandler
from services.games.code_executor import CodeExecutor
from models.games import Game, GameAttempt

logger = logging.getLogger(__name__)

# Security note: For production, use Docker-based execution or external service
# Current implementation has security limitations - see docs/CODE_EXECUTION_SECURITY.md


class CodingGameHandler(BaseGameHandler):
    """Handler for coding challenges and algorithm puzzles."""
    
    def __init__(self):
        # WARNING: Current executor is NOT fully secure for production
        # Consider using secure_code_executor.py or Docker-based solution
        self.code_executor = CodeExecutor(timeout_seconds=10)
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Validate coding challenge content structure.
        
        Supports two formats:
        1. Single question (legacy):
        {
            "description": "Problem description",
            "test_cases": [...],
            "starter_code": "...",
            "language": "python"
        }
        
        2. Multiple questions (new):
        {
            "language": "python",
            "questions": [
                {
                    "description": "Problem description",
                    "test_cases": [...],
                    "starter_code": "...",
                    "function_signature": "...",
                    "concept": "...",
                    "question_number": 1
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
                
                required = ["description", "test_cases", "starter_code"]
                for field in required:
                    if field not in question:
                        logger.warning(f"Question {i} missing required field: {field}")
                        return False
                
                if not isinstance(question["test_cases"], list) or len(question["test_cases"]) == 0:
                    logger.warning(f"Question {i} test_cases must be a non-empty list")
                    return False
                
                # Validate test cases
                for j, test_case in enumerate(question["test_cases"]):
                    if not isinstance(test_case, dict):
                        logger.warning(f"Question {i}, Test case {j} must be a dictionary")
                        return False
                    if "input" not in test_case or "expected_output" not in test_case:
                        logger.warning(f"Question {i}, Test case {j} missing input or expected_output")
                        return False
            
            return True
        
        # Legacy single question format
        required_fields = ["description", "test_cases"]
        for field in required_fields:
            if field not in content:
                logger.warning(f"Missing required field: {field}")
                return False
        
        if not isinstance(content["test_cases"], list) or len(content["test_cases"]) == 0:
            logger.warning("test_cases must be a non-empty list")
            return False
        
        # Validate each test case
        for i, test_case in enumerate(content["test_cases"]):
            if not isinstance(test_case, dict):
                logger.warning(f"Test case {i} must be a dictionary")
                return False
            if "input" not in test_case or "expected_output" not in test_case:
                logger.warning(f"Test case {i} missing input or expected_output")
                return False
        
        return True
    
    async def evaluate_attempt(
        self,
        game: Game,
        attempt: GameAttempt
    ) -> Dict[str, Any]:
        """
        Evaluate user's code submission.
        
        Supports both single question and multi-question formats.
        
        Args:
            game: The coding challenge game
            attempt: User's code submission
            
        Returns:
            Evaluation result with test results
        """
        content = game.game_content
        answer_data = attempt.answer_data
        
        code = answer_data.get("code", "").strip()
        language = answer_data.get("language", content.get("language", "python"))
        question_index = answer_data.get("question_index", None)  # For multi-question games
        
        if not code:
            return {
                "passed": False,
                "error": "No code submitted",
                "test_results": [],
                "total_tests": 0,
                "passed_tests": 0,
                "question_index": question_index
            }
        
        # Check if it's multi-question format
        if "questions" in content:
            if question_index is None:
                return {
                    "passed": False,
                    "error": "question_index required for multi-question games",
                    "test_results": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "question_index": question_index
                }
            
            questions = content["questions"]
            if question_index < 0 or question_index >= len(questions):
                return {
                    "passed": False,
                    "error": f"Invalid question_index: {question_index}",
                    "test_results": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "question_index": question_index
                }
            
            question = questions[question_index]
            test_cases = question.get("test_cases", [])
            
            if not test_cases:
                return {
                    "passed": False,
                    "error": f"No test cases defined for question {question_index + 1}",
                    "test_results": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "question_index": question_index
                }
        else:
            # Legacy single question format
            test_cases = content.get("test_cases", [])
            
            if not test_cases:
                return {
                    "passed": False,
                    "error": "No test cases defined for this challenge",
                    "test_results": [],
                    "total_tests": 0,
                    "passed_tests": 0,
                    "question_index": question_index
                }
        
        # Execute code based on language
        try:
            if language.lower() == "python":
                result = await self.code_executor.execute_python(code, test_cases)
            elif language.lower() in ["javascript", "js"]:
                result = await self.code_executor.execute_javascript(code, test_cases)
            else:
                return {
                    "passed": False,
                    "error": f"Unsupported language: {language}",
                    "test_results": [],
                    "total_tests": len(test_cases),
                    "passed_tests": 0,
                    "question_index": question_index
                }
            
            # Add feedback and question index
            result["feedback"] = self._generate_feedback(result)
            result["question_index"] = question_index
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            return {
                "passed": False,
                "error": f"Execution error: {str(e)}",
                "test_results": [],
                "total_tests": len(test_cases),
                "passed_tests": 0,
                "question_index": question_index
            }
    
    def calculate_score(self, evaluation_result: Dict[str, Any]) -> int:
        """
        Calculate score based on test results.
        
        Scoring:
        - 100 points if all tests pass
        - Partial points based on percentage of tests passed
        """
        if not evaluation_result:
            return 0
        
        if evaluation_result.get("passed", False):
            return 100
        
        total_tests = evaluation_result.get("total_tests", 0)
        passed_tests = evaluation_result.get("passed_tests", 0)
        
        if total_tests == 0:
            return 0
        
        # Calculate percentage and round to nearest integer
        percentage = (passed_tests / total_tests) * 100
        return int(percentage)
    
    def _generate_feedback(self, result: Dict[str, Any]) -> str:
        """Generate feedback message based on test results."""
        total = result.get("total_tests", 0)
        passed = result.get("passed_tests", 0)
        
        if passed == total:
            return f"🎉 Excellent! All {total} test cases passed!"
        elif passed > 0:
            return f"Good progress! {passed} out of {total} test cases passed. Keep working on the remaining cases."
        else:
            return f"None of the test cases passed. Review your logic and try again. Check the expected outputs for hints."
    
    def get_default_content_template(self) -> Dict[str, Any]:
        """Get default content template for coding challenges."""
        return {
            "language": "python",
            "questions": [
                {
                    "description": "Solve the following problem:",
                    "test_cases": [
                        {
                            "name": "Test 1",
                            "input": {},
                            "expected_output": None
                        }
                    ],
                    "starter_code": "def solution():\n    # Your code here\n    pass",
                    "function_signature": "def solution():",
                    "concept": "basic programming",
                    "question_number": 1
                }
            ]
        }

