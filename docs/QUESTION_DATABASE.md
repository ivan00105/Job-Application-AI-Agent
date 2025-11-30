# Coding Questions Database

## Overview

The system now includes a separate database for coding questions that allows you to:
- Store a pool of questions that can be randomly selected
- Seed questions manually or via scripts
- Track question usage and success rates
- Reuse questions across multiple games

## Database Schema

The `coding_questions` table stores:
- **Question content**: description, starter code, test cases, hints
- **Metadata**: language, difficulty, concept, tags
- **Analytics**: usage count, success rate
- **Source tracking**: manual, LLM, or imported

## Usage

### 1. Run Migration

First, create the questions table:

```bash
python backend/scripts/run_questions_migration.py
```

### 2. Seed Sample Questions

Add initial questions to the database:

```bash
python backend/scripts/seed/seed_coding_questions.py
```

### 3. Add More Questions

#### Option A: Edit the Seeding Script

Edit `backend/scripts/seed/seed_coding_questions.py` and add questions to the `SAMPLE_QUESTIONS` list:

```python
{
    "language": "python",
    "difficulty": "beginner",
    "concept": "your concept",
    "description": "Question description...",
    "function_signature": "def your_function(params):",
    "starter_code": "def your_function(params):\n    # Your code here\n    pass",
    "test_cases": [
        {"name": "Test 1", "input": {"param": value}, "expected_output": result}
    ],
    "hints": ["Hint 1", "Hint 2"],
    "points": 20,
    "estimated_time_minutes": 5
}
```

Then run the seeding script again.

#### Option B: Use Interactive Script

Add questions interactively:

```bash
python backend/scripts/admin-tools/add_question.py
```

#### Option C: Use the API (Programmatically)

```python
from services.games.question_database import question_database

question_id = await question_database.add_question(
    language="python",
    difficulty="beginner",
    concept="your concept",
    description="Question description",
    starter_code="def solution():\n    pass",
    test_cases=[...],
    # ... other fields
)
```

## How Games Use Questions

When creating games (via `seed_language_games.py`):

1. **First**: Tries to get questions from the database
2. **If enough questions exist**: Uses random questions from database
3. **If not enough**: Falls back to LLM generation
4. **If LLM fails**: Uses whatever questions are available from database

This ensures:
- Games always have questions (if database has any)
- Questions are randomly selected for variety
- LLM is used as a fallback when needed

## Querying Questions

### Get Questions by Filters

```python
from services.games.question_database import question_database

# Get all Python beginner questions
questions = await question_database.get_questions(
    language="python",
    difficulty="beginner"
)

# Get random questions
random_questions = await question_database.get_random_questions(
    language="python",
    difficulty="beginner",
    num_questions=5
)
```

## Question Structure

Each question should have:

```python
{
    "language": "python" | "javascript",
    "difficulty": "beginner" | "intermediate" | "advanced",
    "concept": "string describing the concept",
    "description": "Full problem description with examples",
    "function_signature": "def function_name(params):",  # Optional
    "starter_code": "def function_name(params):\n    pass",
    "test_cases": [
        {
            "name": "Test 1",
            "input": {"param1": value1, "param2": value2},
            "expected_output": expected_result
        }
    ],
    "hints": ["Hint 1", "Hint 2"],  # Optional
    "points": 20,  # Points for this question
    "estimated_time_minutes": 5
}
```

## Best Practices

1. **Add diverse questions**: Cover different concepts for each language/difficulty
2. **Include good test cases**: At least 3-5 test cases covering edge cases
3. **Write clear descriptions**: Include examples and expected behavior
4. **Provide hints**: Help users who get stuck
5. **Tag appropriately**: Use tags for better organization and filtering

## Analytics

The database tracks:
- **usage_count**: How many times a question has been used
- **success_rate**: Percentage of users who passed (updated after attempts)

Use this data to:
- Identify difficult questions
- Find popular concepts
- Improve question quality

## Migration

To add the questions database to an existing system:

```bash
# 1. Run migration
python backend/scripts/run_questions_migration.py

# 2. Seed initial questions
python backend/scripts/seed/seed_coding_questions.py

# 3. (Optional) Regenerate games to use database questions
# Delete existing games first, then:
python backend/scripts/seed/seed_language_games.py
```

