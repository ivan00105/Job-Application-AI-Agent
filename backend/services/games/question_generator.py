"""
Service for generating coding questions using LLM.
"""
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Try to import LLM service
try:
    # Import from jobs-finder module
    import sys
    import os
    # Add the jobs-finder directory to path if needed
    jobs_finder_path = os.path.join(os.path.dirname(__file__), '..', 'jobs-finder')
    if jobs_finder_path not in sys.path:
        sys.path.insert(0, jobs_finder_path)
    
    from llm_service import llm_service
    
    # Try to get question generator model from config
    try:
        from backend.config import get_settings
        settings = get_settings()
        _QUESTION_GENERATOR_MODEL = getattr(settings, 'openrouter_question_generator_model', None) or os.getenv("OPENROUTER_QUESTION_GENERATOR_MODEL", None)
    except:
        _QUESTION_GENERATOR_MODEL = os.getenv("OPENROUTER_QUESTION_GENERATOR_MODEL", None)
    
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False
    _QUESTION_GENERATOR_MODEL = None
    logger.warning("LLM service not available - question generation will use fallback")


class QuestionGenerator:
    """Service for generating coding questions dynamically."""
    
    # Predefined concepts by language and difficulty
    CONCEPTS = {
        "python": {
            "beginner": [
                "variables and data types",
                "basic operators",
                "if-else statements",
                "for loops",
                "while loops",
                "lists and list methods",
                "dictionaries",
                "string manipulation",
                "functions",
                "list comprehensions"
            ],
            "intermediate": [
                "object-oriented programming",
                "inheritance",
                "decorators",
                "generators",
                "exception handling",
                "file I/O",
                "regular expressions",
                "lambda functions",
                "map, filter, reduce",
                "modules and packages"
            ],
            "advanced": [
                "metaclasses",
                "context managers",
                "async/await",
                "multithreading",
                "multiprocessing",
                "design patterns",
                "memory management",
                "optimization techniques",
                "advanced data structures",
                "algorithm complexity"
            ]
        },
        "javascript": {
            "beginner": [
                "variables (let, const, var)",
                "data types",
                "operators",
                "conditionals",
                "loops",
                "arrays and array methods",
                "objects",
                "functions",
                "arrow functions",
                "template literals"
            ],
            "intermediate": [
                "closures",
                "this keyword",
                "prototypes",
                "classes",
                "promises",
                "async/await",
                "destructuring",
                "spread operator",
                "higher-order functions",
                "event handling"
            ],
            "advanced": [
                "design patterns",
                "functional programming",
                "currying",
                "memoization",
                "generators",
                "proxies",
                "reflection",
                "performance optimization",
                "memory management",
                "advanced async patterns"
            ]
        }
    }
    
    def __init__(self):
        self.llm_available = _LLM_AVAILABLE
    
    def get_concepts(self, language: str, difficulty: str) -> List[str]:
        """Get predefined concepts for a language and difficulty level."""
        language_lower = language.lower()
        difficulty_lower = difficulty.lower()
        
        if language_lower not in self.CONCEPTS:
            logger.warning(f"Language {language} not supported, using Python concepts")
            language_lower = "python"
        
        if difficulty_lower not in self.CONCEPTS[language_lower]:
            logger.warning(f"Difficulty {difficulty} not found, using beginner")
            difficulty_lower = "beginner"
        
        return self.CONCEPTS[language_lower][difficulty_lower]
    
    async def generate_question(
        self,
        language: str,
        difficulty: str,
        concept: str,
        question_number: int = 1
    ) -> Dict[str, Any]:
        """
        Generate a coding question for a specific concept.
        
        Args:
            language: Programming language (python, javascript)
            difficulty: Difficulty level (beginner, intermediate, advanced)
            concept: The concept to test
            question_number: Question number in the set
            
        Returns:
            Question dictionary with description, function signature, starter code, and test cases
        """
        if not self.llm_available:
            return self._generate_fallback_question(language, difficulty, concept, question_number)
        
        try:
            system_prompt = """You are an expert programming instructor. Generate coding questions that test specific programming concepts.
Return your response as a JSON object with the following structure:
{
    "description": "Clear problem description with examples",
    "function_signature": "def function_name(params):",
    "starter_code": "def function_name(params):\n    # Your code here\n    pass",
    "test_cases": [
        {
            "name": "Test 1",
            "input": {"param1": value1, "param2": value2},
            "expected_output": expected_result
        }
    ],
    "hints": ["Optional hint 1", "Optional hint 2"]
}

Make sure:
- The problem clearly tests the specified concept
- Test cases cover edge cases
- Function signature is clear
- Starter code includes the function signature with a pass statement
- For Python: use proper Python syntax
- For JavaScript: use modern ES6+ syntax
- Include 3-5 test cases
- Difficulty should match the specified level"""
            
            user_prompt = f"""Generate a {difficulty} level {language} coding question that tests: {concept}

Requirements:
- Language: {language}
- Difficulty: {difficulty}
- Concept: {concept}
- Question number: {question_number}

Return ONLY valid JSON, no markdown formatting."""
            
            # Use question generator model if configured, otherwise use default
            model_to_use = _QUESTION_GENERATOR_MODEL if _QUESTION_GENERATOR_MODEL else None
            
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.7,
                model=model_to_use
            )
            
            # Parse JSON response
            # Remove markdown code fences if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            question_data = json.loads(response)
            
            # Validate structure
            if not self._validate_question(question_data):
                logger.warning("Generated question failed validation, using fallback")
                return self._generate_fallback_question(language, difficulty, concept, question_number)
            
            # Add metadata
            question_data["concept"] = concept
            question_data["language"] = language
            question_data["difficulty"] = difficulty
            question_data["question_number"] = question_number
            
            return question_data
            
        except Exception as e:
            logger.error(f"Error generating question with LLM: {e}")
            return self._generate_fallback_question(language, difficulty, concept, question_number)
    
    def _validate_question(self, question_data: Dict[str, Any]) -> bool:
        """Validate that question has required fields."""
        required = ["description", "function_signature", "starter_code", "test_cases"]
        for field in required:
            if field not in question_data:
                return False
        
        if not isinstance(question_data.get("test_cases"), list) or len(question_data["test_cases"]) == 0:
            return False
        
        return True
    
    def _generate_fallback_question(
        self,
        language: str,
        difficulty: str,
        concept: str,
        question_number: int
    ) -> Dict[str, Any]:
        """Generate a simple fallback question when LLM is not available."""
        if language.lower() == "python":
            return {
                "description": f"Implement a function that demonstrates {concept}. This is a {difficulty} level question.",
                "function_signature": f"def solution_{question_number}(*args, **kwargs):",
                "starter_code": f"def solution_{question_number}(*args, **kwargs):\n    # Implement {concept}\n    pass",
                "test_cases": [
                    {
                        "name": "Test 1",
                        "input": {},
                        "expected_output": None
                    }
                ],
                "concept": concept,
                "language": language,
                "difficulty": difficulty,
                "question_number": question_number
            }
        else:  # JavaScript
            return {
                "description": f"Implement a function that demonstrates {concept}. This is a {difficulty} level question.",
                "function_signature": f"function solution{question_number}(...args) {{}}",
                "starter_code": f"function solution{question_number}(...args) {{\n    // Implement {concept}\n    return null;\n}}",
                "test_cases": [
                    {
                        "name": "Test 1",
                        "input": {},
                        "expected_output": None
                    }
                ],
                "concept": concept,
                "language": language,
                "difficulty": difficulty,
                "question_number": question_number
            }
    
    async def generate_question_set(
        self,
        language: str,
        difficulty: str,
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate a set of random questions for a language and difficulty.
        
        Args:
            language: Programming language
            difficulty: Difficulty level
            num_questions: Number of questions to generate
            
        Returns:
            List of question dictionaries
        """
        import random
        
        concepts = self.get_concepts(language, difficulty)
        
        # Randomly select concepts (with replacement if needed)
        selected_concepts = random.choices(concepts, k=num_questions)
        
        questions = []
        for i, concept in enumerate(selected_concepts, 1):
            question = await self.generate_question(language, difficulty, concept, i)
            questions.append(question)
        
        return questions


# Singleton instance
question_generator = QuestionGenerator()

