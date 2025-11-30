"""
Service for managing multiple choice questions database.
"""
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from database.postgres_client import get_postgres_client

logger = logging.getLogger(__name__)


class MultipleChoiceQuestionDatabase:
    """Service for managing multiple choice questions in the database."""
    
    async def add_question(
        self,
        topic: str,
        category: str,
        difficulty: str,
        question_text: str,
        options: List[Dict[str, str]],  # [{"text": "Option A", "id": "a"}, ...]
        correct_answer: str,  # ID of correct option
        explanation: Optional[str] = None,
        points: int = 10,
        estimated_time_minutes: int = 2,
        tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        source: str = "manual",
        created_by: Optional[str] = None
    ) -> str:
        """
        Add a new multiple choice question to the database.
        
        Returns:
            Question ID (UUID string)
        """
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        question_id = str(uuid.uuid4())
        
        await db.execute(
            """INSERT INTO multiple_choice_questions 
               (id, topic, category, difficulty, question_text, options, correct_answer,
                explanation, points, estimated_time_minutes, tags, domain, source, created_by, is_active)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10, $11, $12, $13, $14, $15)""",
            question_id,
            topic,
            category,
            difficulty,
            question_text,
            json.dumps(options),
            correct_answer,
            explanation,
            points,
            estimated_time_minutes,
            tags or [],
            domain,
            source,
            created_by,
            True
        )
        
        logger.info(f"Added MC question {question_id} for {topic} {difficulty} - {category}")
        return question_id
    
    async def get_questions(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        domain: Optional[str] = None,
        limit: Optional[int] = None,
        random: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get questions from the database with optional filters.
        
        Args:
            topic: Filter by topic (e.g., "Python", "Logic")
            category: Filter by category (e.g., "technical", "language", "logic")
            difficulty: Filter by difficulty level
            domain: Filter by domain (IT, Finance, General)
            limit: Maximum number of questions to return
            random: If True, return questions in random order
            
        Returns:
            List of question dictionaries
        """
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        conditions = ["is_active = TRUE"]
        params = []
        param_num = 1
        
        if topic:
            conditions.append(f"topic = ${param_num}")
            params.append(topic)
            param_num += 1
        
        if category:
            conditions.append(f"category = ${param_num}")
            params.append(category)
            param_num += 1
        
        if difficulty:
            conditions.append(f"difficulty = ${param_num}")
            params.append(difficulty)
            param_num += 1
        
        if domain:
            conditions.append(f"domain = ${param_num}")
            params.append(domain)
            param_num += 1
        
        order_by = "RANDOM()" if random else "created_at DESC"
        limit_clause = f"LIMIT ${param_num}" if limit else ""
        if limit:
            params.append(limit)
        
        query = f"""
            SELECT * FROM multiple_choice_questions 
            WHERE {' AND '.join(conditions)}
            ORDER BY {order_by}
            {limit_clause}
        """
        
        rows = await db.fetch_all(query, *params)
        
        questions = []
        for row in rows:
            question_dict = dict(row)
            # Convert UUID to string
            if question_dict.get("id"):
                question_dict["id"] = str(question_dict["id"])
            if question_dict.get("created_by"):
                question_dict["created_by"] = str(question_dict["created_by"])
            # Parse JSONB fields
            if isinstance(question_dict.get("options"), str):
                try:
                    question_dict["options"] = json.loads(question_dict["options"])
                except:
                    question_dict["options"] = []
            # Convert datetime
            if question_dict.get("created_at") and hasattr(question_dict["created_at"], "isoformat"):
                question_dict["created_at"] = question_dict["created_at"].isoformat()
            if question_dict.get("updated_at") and hasattr(question_dict["updated_at"], "isoformat"):
                question_dict["updated_at"] = question_dict["updated_at"].isoformat()
            
            questions.append(question_dict)
        
        return questions
    
    async def get_random_questions(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        domain: Optional[str] = None,
        num_questions: int = 10,
        exclude_topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get random questions for a topic/category and difficulty.
        
        Args:
            topic: Topic filter
            category: Category filter
            difficulty: Difficulty level
            domain: Domain filter
            num_questions: Number of questions to return
            exclude_topics: Topics to exclude (to avoid duplicates)
            
        Returns:
            List of question dictionaries
        """
        # Get all available questions
        all_questions = await self.get_questions(
            topic=topic,
            category=category,
            difficulty=difficulty,
            domain=domain,
            random=True
        )
        
        # Filter out excluded topics if provided
        if exclude_topics:
            all_questions = [q for q in all_questions if q.get("topic") not in exclude_topics]
        
        # Return up to num_questions
        return all_questions[:num_questions]
    
    async def increment_usage(self, question_id: str):
        """Increment the usage count for a question."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        await db.execute(
            "UPDATE multiple_choice_questions SET usage_count = usage_count + 1, updated_at = $1 WHERE id = $2",
            datetime.now(timezone.utc),
            question_id
        )
    
    async def update_success_rate(self, question_id: str, success_rate: float):
        """Update the success rate for a question."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        await db.execute(
            "UPDATE multiple_choice_questions SET success_rate = $1, updated_at = $2 WHERE id = $3",
            success_rate,
            datetime.now(timezone.utc),
            question_id
        )


# Singleton instance
multiple_choice_question_database = MultipleChoiceQuestionDatabase()

