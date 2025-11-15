"""
Interview service - AI evaluation and question management.
"""
import json
import httpx
import logging
import time
from typing import Optional, List, Dict, Any

from config import get_settings
from models.interview import (
    EvaluationScores,
    InterviewQuestion,
    DomainType,
    QuestionCategory
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Import LLM logger
try:
    from backend.services.shared.llm_logger import log_llm_call
except ImportError:
    try:
        from services.shared.llm_logger import log_llm_call
    except ImportError:
        # Fallback if logger not available
        def log_llm_call(*args, **kwargs):
            pass


class InterviewService:
    """Service for AI-powered interview evaluation and question generation."""

    def __init__(self):
        self.openrouter_api_key = settings.openrouter_api_key
        self.openrouter_base_url = settings.openrouter_base_url or "https://openrouter.ai/api/v1"
        # Use gpt-oss-120b model (can be openrouter/gpt-oss-120b or openai/gpt-oss-120b)
        self.openrouter_model = settings.openrouter_model or "openrouter/gpt-oss-120b"
        self.http_referer = getattr(settings, 'openrouter_http_referer', None)
        
    async def _call_openrouter(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[str] = None
    ) -> str:
        """Call OpenRouter API for text generation."""
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        json_data = {
            "model": self.openrouter_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add response_format if specified (for JSON mode)
        if response_format:
            json_data["response_format"] = {"type": response_format}
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "HTTP-Referer": self.http_referer or "https://github.com/your-repo",
                        "X-Title": "Job Application AI Agent"
                    },
                    json=json_data
                )
                response.raise_for_status()
                data = response.json()
                
                duration_ms = (time.time() - start_time) * 1000
                generated_text = data["choices"][0]["message"]["content"].strip()
                
                # Extract token usage if available
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")
                
                # Log the LLM call
                log_llm_call(
                    provider="openrouter",
                    model=self.openrouter_model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    response=generated_text,
                    request_data=json_data,
                    response_data=data,
                    duration_ms=duration_ms,
                    tokens_used=tokens_used,
                    metadata={"function": "_call_openrouter", "response_format": response_format}
                )
                
                return generated_text
                
        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"OpenRouter API call failed: {error_msg}")
            
            # Log the error
            log_llm_call(
                provider="openrouter",
                model=self.openrouter_model,
                prompt=prompt,
                system_prompt=system_prompt,
                error=error_msg,
                request_data=json_data,
                duration_ms=duration_ms,
                metadata={"function": "_call_openrouter", "response_format": response_format}
            )
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"Unexpected error in OpenRouter API call: {error_msg}")
            
            # Log the error
            log_llm_call(
                provider="openrouter",
                model=self.openrouter_model,
                prompt=prompt,
                system_prompt=system_prompt,
                error=error_msg,
                request_data=json_data,
                duration_ms=duration_ms,
                metadata={"function": "_call_openrouter", "response_format": response_format}
            )
            raise

    async def evaluate_answer(
        self,
        question: InterviewQuestion,
        user_answer: str,
        knowledge_context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate user's interview answer using AI with RAG context.

        Args:
            question: The interview question
            user_answer: User's response
            knowledge_context: Retrieved knowledge from RAG system

        Returns:
            Dictionary with scores, feedback, strengths, and improvements
        """
        context_str = ""
        if knowledge_context:
            context_str = "\n\nRelevant domain knowledge:\n" + "\n".join(knowledge_context)

        ideal_answer_str = f"\n\nIdeal answer reference:\n{question.ideal_answer}" if question.ideal_answer else ""

        evaluation_prompt = f"""You are an expert interviewer evaluating a candidate's response for a {question.domain} {question.category} interview question.

Question: {question.question_text}
Difficulty Level: {question.difficulty}
Role Type: {question.role_type}
{ideal_answer_str}
{context_str}

Candidate's Answer:
{user_answer}

Please evaluate this answer on the following dimensions (score 1-5 for each):
1. Relevance (1=off-topic, 5=directly addresses question)
2. Completeness (1=incomplete, 5=comprehensive coverage)
3. Technical Accuracy (1=incorrect, 5=technically sound)
4. Communication (1=unclear, 5=articulate and well-structured)

Also provide:
- Overall score (1-5, weighted average)
- 2-3 specific strengths
- 2-3 specific areas for improvement
- Constructive feedback paragraph (2-3 sentences)

Return your evaluation in the following JSON format:
{{
    "overall_score": 4.2,
    "relevance_score": 4.5,
    "completeness_score": 4.0,
    "technical_accuracy_score": 4.3,
    "communication_score": 4.0,
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "improvements": ["improvement 1", "improvement 2", "improvement 3"],
    "feedback": "Detailed feedback paragraph here."
}}

Be constructive, specific, and encouraging in your feedback."""

        try:
            if self.openrouter_api_key:
                system_prompt = "You are an expert interviewer providing constructive evaluation."
                response_text = await self._call_openrouter(
                    prompt=evaluation_prompt,
                    system_prompt=system_prompt,
                    temperature=0.7,
                    max_tokens=2000,
                    response_format="json_object"
                )
                result = json.loads(response_text)
                return result
            else:
                logger.warning("OpenRouter API key not configured, using mock evaluation")
                return self._mock_evaluation()

        except Exception as e:
            logger.error(f"Error in AI evaluation: {e}")
            return self._mock_evaluation()

    def _mock_evaluation(self) -> Dict[str, Any]:
        """Mock evaluation for testing without API keys."""
        return {
            "overall_score": 3.5,
            "relevance_score": 4.0,
            "completeness_score": 3.5,
            "technical_accuracy_score": 3.5,
            "communication_score": 3.0,
            "strengths": [
                "Clear structure in your answer",
                "Relevant examples provided",
                "Good understanding of core concepts"
            ],
            "improvements": [
                "Could provide more technical depth",
                "Consider discussing trade-offs or alternative approaches",
                "Expand on real-world applications"
            ],
            "feedback": "Your answer demonstrates a solid foundation, but could benefit from more technical detail and deeper analysis. Consider structuring your response with specific examples and discussing potential challenges or edge cases."
        }

    async def generate_question(
        self,
        domain: DomainType,
        role_type: str,
        difficulty: str,
        job_context: Optional[str] = None
    ) -> InterviewQuestion:
        """
        Generate a custom interview question based on job context.
        This is useful for job-specific interview prep.
        """
        context_str = f"\n\nJob Context:\n{job_context}" if job_context else ""

        prompt = f"""Generate a {difficulty} level {domain} interview question for a {role_type} role.
{context_str}

The question should be realistic, relevant, and appropriate for the difficulty level.
Include an ideal answer that covers key points a good candidate would mention.

Return in JSON format:
{{
    "question_text": "The interview question",
    "category": "technical|behavioral|case_study|situational|coding",
    "ideal_answer": "A comprehensive ideal answer"
}}"""

        try:
            if self.openrouter_api_key:
                system_prompt = "You are an expert interviewer creating realistic interview questions."
                response_text = await self._call_openrouter(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.8,
                    max_tokens=2000,
                    response_format="json_object"
                )
                result = json.loads(response_text)

                return InterviewQuestion(
                    question_text=result["question_text"],
                    role_type=role_type,
                    domain=domain,
                    category=result["category"],
                    difficulty=difficulty,
                    ideal_answer=result.get("ideal_answer")
                )
            else:
                logger.warning("OpenRouter API key not configured, using mock question")
                return self._mock_question(domain, role_type, difficulty)

        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return self._mock_question(domain, role_type, difficulty)

    def _mock_question(self, domain: DomainType, role_type: str, difficulty: str) -> InterviewQuestion:
        """Mock question for testing."""
        questions_bank = {
            "IT": {
                "beginner": "Explain the difference between a stack and a queue data structure.",
                "intermediate": "How would you design a scalable REST API for a social media platform?",
                "advanced": "Describe how you would implement a distributed caching system with cache invalidation."
            },
            "Finance": {
                "beginner": "What is the difference between a balance sheet and an income statement?",
                "intermediate": "How would you value a company using discounted cash flow analysis?",
                "advanced": "Explain the Black-Scholes model and its assumptions for option pricing."
            }
        }

        question_text = questions_bank.get(domain, {}).get(difficulty, "Tell me about your experience in this field.")

        return InterviewQuestion(
            question_text=question_text,
            role_type=role_type,
            domain=domain,
            category=QuestionCategory.TECHNICAL,
            difficulty=difficulty,
            ideal_answer="A comprehensive answer would cover key concepts and provide relevant examples."
        )


interview_service = InterviewService()
