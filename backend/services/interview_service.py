"""
Interview service - AI evaluation and question management.
"""
import json
from typing import Optional, List, Dict, Any
from openai import OpenAI
from anthropic import Anthropic

from config import get_settings
from models.interview import (
    EvaluationScores,
    InterviewQuestion,
    DomainType,
    QuestionCategory
)

settings = get_settings()


class InterviewService:
    """Service for AI-powered interview evaluation and question generation."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key) if hasattr(settings, 'openai_api_key') else None
        self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key) if hasattr(settings, 'anthropic_api_key') else None

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
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert interviewer providing constructive evaluation."},
                        {"role": "user", "content": evaluation_prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)
                return result
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": evaluation_prompt}
                    ]
                )
                result = json.loads(response.content[0].text)
                return result
            else:
                return self._mock_evaluation()

        except Exception as e:
            print(f"Error in AI evaluation: {e}")
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
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert interviewer creating realistic interview questions."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)

                return InterviewQuestion(
                    question_text=result["question_text"],
                    role_type=role_type,
                    domain=domain,
                    category=result["category"],
                    difficulty=difficulty,
                    ideal_answer=result.get("ideal_answer")
                )
            else:
                return self._mock_question(domain, role_type, difficulty)

        except Exception as e:
            print(f"Error generating question: {e}")
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
