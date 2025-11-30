"""
Service for managing coding questions database.
"""
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from database.postgres_client import get_postgres_client

logger = logging.getLogger(__name__)


class QuestionDatabase:
    """Service for managing coding questions in the database."""
    
    async def add_question(
        self,
        language: str,
        difficulty: str,
        concept: str,
        description: str,
        starter_code: str,
        test_cases: List[Dict[str, Any]],
        function_signature: Optional[str] = None,
        hints: Optional[List[str]] = None,
        points: int = 20,
        estimated_time_minutes: int = 5,
        tags: Optional[List[str]] = None,
        source: str = "manual",
        created_by: Optional[str] = None
    ) -> str:
        """
        Add a new question to the database.
        
        Returns:
            Question ID (UUID string)
        """
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        question_id = str(uuid.uuid4())
        
        await db.execute(
            """INSERT INTO coding_questions 
               (id, language, difficulty, concept, description, function_signature, 
                starter_code, test_cases, hints, points, estimated_time_minutes, 
                tags, source, created_by, is_active)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10, $11, $12, $13, $14, $15)""",
            question_id,
            language,
            difficulty,
            concept,
            description,
            function_signature,
            starter_code,
            json.dumps(test_cases),
            json.dumps(hints or []),
            points,
            estimated_time_minutes,
            tags or [],
            source,
            created_by,
            True
        )
        
        logger.info(f"Added question {question_id} for {language} {difficulty} - {concept}")
        return question_id
    
    async def get_questions(
        self,
        language: Optional[str] = None,
        difficulty: Optional[str] = None,
        concept: Optional[str] = None,
        limit: Optional[int] = None,
        random: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get questions from the database with optional filters.
        
        Args:
            language: Filter by programming language
            difficulty: Filter by difficulty level
            concept: Filter by concept
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
        
        if language:
            conditions.append(f"language = ${param_num}")
            params.append(language)
            param_num += 1
        
        if difficulty:
            conditions.append(f"difficulty = ${param_num}")
            params.append(difficulty)
            param_num += 1
        
        if concept:
            conditions.append(f"concept = ${param_num}")
            params.append(concept)
            param_num += 1
        
        order_by = "RANDOM()" if random else "created_at DESC"
        limit_clause = f"LIMIT ${param_num}" if limit else ""
        if limit:
            params.append(limit)
        
        query = f"""
            SELECT * FROM coding_questions 
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
            if isinstance(question_dict.get("test_cases"), str):
                try:
                    question_dict["test_cases"] = json.loads(question_dict["test_cases"])
                except:
                    question_dict["test_cases"] = []
            if isinstance(question_dict.get("hints"), str):
                try:
                    question_dict["hints"] = json.loads(question_dict["hints"])
                except:
                    question_dict["hints"] = []
            # Convert datetime
            if question_dict.get("created_at") and hasattr(question_dict["created_at"], "isoformat"):
                question_dict["created_at"] = question_dict["created_at"].isoformat()
            if question_dict.get("updated_at") and hasattr(question_dict["updated_at"], "isoformat"):
                question_dict["updated_at"] = question_dict["updated_at"].isoformat()
            
            questions.append(question_dict)
        
        return questions
    
    async def get_random_questions(
        self,
        language: str,
        difficulty: str,
        num_questions: int = 5,
        exclude_concepts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get random questions for a language and difficulty.
        
        Args:
            language: Programming language
            difficulty: Difficulty level
            num_questions: Number of questions to return
            exclude_concepts: Concepts to exclude (to avoid duplicates)
            
        Returns:
            List of question dictionaries
        """
        # Get all available questions
        all_questions = await self.get_questions(
            language=language,
            difficulty=difficulty,
            random=True
        )
        
        # Filter out excluded concepts if provided
        if exclude_concepts:
            all_questions = [q for q in all_questions if q.get("concept") not in exclude_concepts]
        
        # Return up to num_questions
        return all_questions[:num_questions]
    
    async def increment_usage(self, question_id: str):
        """Increment the usage count for a question."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        await db.execute(
            "UPDATE coding_questions SET usage_count = usage_count + 1, updated_at = $1 WHERE id = $2",
            datetime.now(timezone.utc),
            question_id
        )
    
    async def update_success_rate(self, question_id: str, success_rate: float):
        """Update the success rate for a question."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        await db.execute(
            "UPDATE coding_questions SET success_rate = $1, updated_at = $2 WHERE id = $2",
            success_rate,
            datetime.now(timezone.utc),
            question_id
        )
    
    async def delete_question(self, question_id: str) -> bool:
        """Soft delete a question (set is_active to False)."""
        db = get_postgres_client()
        if db.pool is None:
            await db.connect()
        
        result = await db.execute(
            "UPDATE coding_questions SET is_active = FALSE, updated_at = $1 WHERE id = $2",
            datetime.now(timezone.utc),
            question_id
        )
        
        return result > 0


# Singleton instance
question_database = QuestionDatabase()

