"""
Memory service for storing and retrieving user's form answers.
"""
from typing import Optional, List, Dict, Any
from database.postgres_client import PostgresClient
import json


async def get_memory(
    db: PostgresClient,
    user_id: str,
    field_label: Optional[str] = None,
    company_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a specific memory entry for a field.
    Returns the most recent matching memory if found.
    """
    if field_label:
        # Try company-specific first
        if company_name:
            result = await db.fetch_one(
                """SELECT * FROM agent_memory 
                   WHERE user_id = $1 AND question_text = $2 AND company_name = $3
                   ORDER BY updated_at DESC LIMIT 1""",
                user_id, field_label, company_name
            )
            if result:
                return dict(result)
        
        # Fall back to global
        result = await db.fetch_one(
            """SELECT * FROM agent_memory 
               WHERE user_id = $1 AND question_text = $2 AND context_key = 'global'
               ORDER BY updated_at DESC LIMIT 1""",
            user_id, field_label
        )
        if result:
            return dict(result)
    
    return None


async def get_all_memory(
    db: PostgresClient,
    user_id: str,
    company_name: Optional[str] = None,
    context_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all memory entries for a user.
    Can filter by company_name and context_type.
    """
    query = "SELECT * FROM agent_memory WHERE user_id = $1"
    params = [user_id]
    
    if company_name:
        query += " AND company_name = $2"
        params.append(company_name)
    elif context_type == 'global':
        query += " AND context_key = 'global'"
    
    query += " ORDER BY updated_at DESC"
    
    results = await db.fetch_all(query, *params)
    return [dict(row) for row in results]


def clean_field_label(label: str) -> str:
    """Clean field label - remove extra whitespace, newlines, special chars"""
    import re
    if not label:
        return ''
    # Replace multiple whitespace with single space
    label = re.sub(r'\s+', ' ', label)
    # Remove asterisks and colons
    label = re.sub(r'[*:]', '', label)
    # Trim
    return label.strip()


async def save_memory(
    db: PostgresClient,
    user_id: str,
    field_label: str,
    answer: str,
    context_type: str = 'global',
    company_name: Optional[str] = None,
    job_url: Optional[str] = None
) -> str:
    """
    Save or update a memory entry.
    Returns the memory ID.
    """
    # Clean the field label before saving
    field_label = clean_field_label(field_label)
    # Check if exists
    existing = None
    if context_type == 'company' and company_name:
        existing = await db.fetch_one(
            """SELECT id FROM agent_memory 
               WHERE user_id = $1 AND question_text = $2 AND company_name = $3""",
            user_id, field_label, company_name
        )
    else:
        existing = await db.fetch_one(
            """SELECT id FROM agent_memory 
               WHERE user_id = $1 AND question_text = $2 AND context_key = 'global'""",
            user_id, field_label
        )
    
    if existing:
        # Update
        memory_id = existing['id']
        await db.execute(
            """UPDATE agent_memory 
               SET answer_text = $1, job_url = $2, updated_at = NOW()
               WHERE id = $3""",
            answer, job_url, memory_id
        )
    else:
        # Insert
        memory_id = await db.fetch_val(
            """INSERT INTO agent_memory 
               (user_id, context_key, question_text, answer_text, company_name, job_url)
               VALUES ($1, $2, $3, $4, $5, $6)
               RETURNING id""",
            user_id,
            context_type,
            field_label,
            answer,
            company_name,
            job_url
        )
    
    return str(memory_id)


async def delete_memory(
    db: PostgresClient,
    user_id: str,
    memory_id: str
) -> bool:
    """
    Delete a memory entry.
    Returns True if deleted, False if not found.
    """
    result = await db.execute(
        "DELETE FROM agent_memory WHERE id = $1 AND user_id = $2",
        memory_id, user_id
    )
    return result is not None


async def search_similar_memory(
    db: PostgresClient,
    user_id: str,
    field_label: str,
    company_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar questions using fuzzy text matching.
    Useful when exact match not found.
    """
    # Use PostgreSQL's similarity search (trigram)
    query = """
        SELECT *, similarity(question_text, $2) as sim
        FROM agent_memory
        WHERE user_id = $1
    """
    params = [user_id, field_label]
    
    if company_name:
        query += " AND company_name = $3"
        params.append(company_name)
    
    query += " AND similarity(question_text, $2) > 0.3 ORDER BY sim DESC LIMIT 5"
    
    try:
        results = await db.fetch_all(query, *params)
        return [dict(row) for row in results]
    except:
        # If pg_trgm extension not available, return empty
        return []

