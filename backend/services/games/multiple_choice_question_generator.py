"""
Service for generating multiple choice questions using LLM.
"""
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Try to import LLM service
try:
    import sys
    import os
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


class MultipleChoiceQuestionGenerator:
    """Service for generating multiple choice questions dynamically."""
    
    # Predefined topics and categories
    TOPICS = {
        "technical": [
            "Python", "JavaScript", "Java", "C++", "SQL", "HTML/CSS",
            "Data Structures", "Algorithms", "System Design", "Database",
            "Networking", "Security", "DevOps", "Cloud Computing"
        ],
        "language": [
            "English Grammar", "English Vocabulary", "Reading Comprehension",
            "Business English", "Technical Writing"
        ],
        "logic": [
            "Logical Reasoning", "Critical Thinking", "Problem Solving",
            "Pattern Recognition", "Analytical Thinking"
        ],
        "general": [
            "Mathematics", "Statistics", "General Knowledge",
            "Business Concepts", "Project Management"
        ]
    }
    
    CATEGORIES = ["technical", "language", "logic", "general"]
    
    async def generate_question(
        self,
        topic: str,
        category: str,
        difficulty: str,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a single multiple choice question using LLM.
        
        Args:
            topic: Topic for the question (e.g., "Python", "Logic")
            category: Category (technical, language, logic, general)
            difficulty: Difficulty level (beginner, intermediate, advanced)
            domain: Optional domain (IT, Finance, General)
            
        Returns:
            Question dictionary with question_text, options, correct_answer, explanation
        """
        if not _LLM_AVAILABLE:
            logger.warning("LLM not available, returning template question")
            return self._generate_fallback_question(topic, category, difficulty)
        
        try:
            # Build prompt for LLM
            system_prompt = """You are an expert question writer creating high-quality multiple choice questions for job candidate assessments.

Create questions that:
- Test real knowledge and understanding, not just memorization
- Have one clearly correct answer
- Include plausible distractors (wrong answers)
- Are appropriate for the specified difficulty level
- Are relevant to the topic and category

Return your response as a JSON object with this exact structure:
{
    "question_text": "The question text here",
    "options": [
        {"id": "a", "text": "Option A text"},
        {"id": "b", "text": "Option B text"},
        {"id": "c", "text": "Option C text"},
        {"id": "d", "text": "Option D text"}
    ],
    "correct_answer": "a",
    "explanation": "Brief explanation of why the correct answer is right"
}

Always provide exactly 4 options (a, b, c, d)."""
            
            user_prompt = f"""Create a {difficulty}-level multiple choice question about {topic} in the {category} category.
{f"Focus on {domain} domain context." if domain and domain != "General" else ""}

The question should:
- Be clear and unambiguous
- Test practical knowledge or understanding
- Have distractors that are plausible but incorrect
- Be appropriate for {difficulty} level candidates

Return only the JSON object, no additional text."""
            
            # Use question generator model if configured, otherwise use default
            model_to_use = _QUESTION_GENERATOR_MODEL if _QUESTION_GENERATOR_MODEL else None
            
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500,
                model=model_to_use
            )
            
            # Parse response (might have markdown code fences)
            response_text = response.strip()
            if not response_text:
                raise ValueError("Empty response from LLM")
            
            # Remove markdown code fences
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Try to extract JSON if there's extra text
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                response_text = response_text[start:end]
            
            if not response_text:
                raise ValueError("No JSON found in LLM response")
            
            # Try to fix common JSON issues
            # Replace single quotes with double quotes (but be careful with apostrophes in text)
            # This is a simple fix - for production, consider using a more robust JSON repair library
            try:
                question_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                # Try to fix common issues
                # Escape unescaped quotes in strings
                import re
                # Fix unescaped quotes in option text (but preserve escaped quotes)
                fixed_text = re.sub(r'(?<!\\)"(?![,}\]]|$)', '\\"', response_text)
                try:
                    question_data = json.loads(fixed_text)
                except:
                    # If still fails, try to manually extract fields using regex
                    logger.warning(f"JSON parsing failed, attempting manual extraction: {e}")
                    raise ValueError(f"Invalid JSON format: {str(e)}")
            
            # Validate structure
            required_fields = ["question_text", "options", "correct_answer"]
            for field in required_fields:
                if field not in question_data:
                    raise ValueError(f"Missing required field: {field}")
            
            if not isinstance(question_data["options"], list) or len(question_data["options"]) != 4:
                raise ValueError("Must have exactly 4 options")
            
            # Validate correct_answer is one of the option IDs
            option_ids = [opt.get("id") for opt in question_data["options"]]
            if question_data["correct_answer"] not in option_ids:
                raise ValueError(f"correct_answer must be one of {option_ids}")
            
            return question_data
            
        except Exception as e:
            logger.error(f"Error generating question with LLM: {e}")
            # Don't return fallback question - raise error instead
            # This prevents template questions from being saved to database
            raise ValueError(f"Failed to generate question: {e}. Please retry or check LLM service.")
    
    def _generate_fallback_question(
        self,
        topic: str,
        category: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """Generate a template question when LLM is unavailable."""
        return {
            "question_text": f"What is a key concept in {topic} at {difficulty} level?",
            "options": [
                {"id": "a", "text": "Option A (correct)"},
                {"id": "b", "text": "Option B"},
                {"id": "c", "text": "Option C"},
                {"id": "d", "text": "Option D"}
            ],
            "correct_answer": "a",
            "explanation": f"This is a template question for {topic} at {difficulty} level."
        }
    
    async def generate_question_set(
        self,
        topic: str,
        category: str,
        difficulty: str,
        domain: Optional[str] = None,
        num_questions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate a set of random questions for a topic, category, and difficulty.
        
        Args:
            topic: Topic for questions
            category: Category (technical, language, logic, general)
            difficulty: Difficulty level
            domain: Optional domain
            num_questions: Number of questions to generate
            
        Returns:
            List of question dictionaries
        """
        questions = []
        for i in range(num_questions):
            try:
                question = await self.generate_question(topic, category, difficulty, domain)
                questions.append(question)
            except Exception as e:
                logger.error(f"Error generating question {i+1}: {e}")
                continue
        
        return questions


# Singleton instance
multiple_choice_question_generator = MultipleChoiceQuestionGenerator()

