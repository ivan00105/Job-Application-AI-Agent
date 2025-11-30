# Multiple Choice Games Implementation

## Overview

The Multiple Choice game type has been fully implemented with a question bank system similar to coding challenges. Admins can generate questions using LLM, and users get random questions in each session.

## Database Schema

### Multiple Choice Questions Table

The `multiple_choice_questions` table stores:
- **Question content**: question_text, options (JSONB array), correct_answer, explanation
- **Metadata**: topic, category, difficulty, domain, tags
- **Analytics**: usage_count, success_rate
- **Source tracking**: manual, LLM, or imported

### Key Fields

- `topic`: Specific topic (e.g., "Python", "English Grammar", "Logic")
- `category`: Type of question (technical, language, logic, general)
- `difficulty`: beginner, intermediate, advanced
- `domain`: IT, Finance, General (optional)
- `options`: JSONB array of option objects: `[{"id": "a", "text": "Option A"}, ...]`
- `correct_answer`: ID of correct option (e.g., "a", "b", "c", "d")

## Admin Scripts

### 1. Generate Questions Using LLM

**Script**: `backend/scripts/generate_mc_questions.py`

Interactive script for admins to generate questions:

```bash
python backend/scripts/generate_mc_questions.py
```

**Features**:
- Select category (technical, language, logic, general)
- Choose or enter custom topic
- Select difficulty level
- Choose domain (IT, Finance, General)
- Specify number of questions to generate
- Automatically checks for duplicates
- Stores questions in database with LLM source tag

**Example Usage**:
1. Run the script
2. Select category: `1` (technical)
3. Select topic: `1` (Python)
4. Select difficulty: `2` (intermediate)
5. Select domain: `1` (IT)
6. Enter number: `20`
7. Confirm and generate

### 2. Seed Multiple Choice Games

**Script**: `backend/scripts/seed/seed_multiple_choice_games.py`

Creates game entries that use questions from the database:

```bash
python backend/scripts/seed/seed_multiple_choice_games.py
```

**What it does**:
- Creates games for each topic/category/difficulty combination
- Games are configured to use random questions from database
- Questions are selected at session start (10-20 per game based on difficulty)

## Question Generation

### Using LLM Service

The `MultipleChoiceQuestionGenerator` uses the LLM service to generate questions:

```python
from services.games.multiple_choice_question_generator import multiple_choice_question_generator

# Generate a single question
question = await multiple_choice_question_generator.generate_question(
    topic="Python",
    category="technical",
    difficulty="intermediate",
    domain="IT"
)

# Generate multiple questions
questions = await multiple_choice_question_generator.generate_question_set(
    topic="Python",
    category="technical",
    difficulty="intermediate",
    num_questions=10
)
```

### Question Structure

Generated questions follow this format:

```json
{
    "question_text": "What is the time complexity of binary search?",
    "options": [
        {"id": "a", "text": "O(n)"},
        {"id": "b", "text": "O(log n)"},
        {"id": "c", "text": "O(n log n)"},
        {"id": "d", "text": "O(1)"}
    ],
    "correct_answer": "b",
    "explanation": "Binary search eliminates half of the search space in each iteration, resulting in O(log n) time complexity."
}
```

## How Games Work

### Session Start

When a user starts a multiple choice game session:

1. System checks game configuration (topic, category, difficulty, domain)
2. Randomly selects questions from database matching the criteria
3. Stores selected questions in session's `result_data`
4. User sees these questions in order

### Question Selection

Questions are selected based on:
- Game's `topic` (from game_content)
- Game's `category` (from game_content)
- Game's `difficulty` (from game.difficulty)
- Game's `domain` (from game.domain)

### Answer Evaluation

When user submits an answer:
- Handler compares `selected_answer` with `correct_answer`
- Returns evaluation result with correctness
- Calculates score (10 points per question, full score if all correct)

## Categories and Topics

### Technical
- Python, JavaScript, Java, SQL
- Data Structures, Algorithms
- System Design, Database, Networking

### Language
- English Grammar, Vocabulary
- Reading Comprehension
- Business English, Technical Writing

### Logic
- Logical Reasoning
- Critical Thinking
- Problem Solving, Pattern Recognition

### General
- Mathematics, Statistics
- General Knowledge
- Business Concepts, Project Management

## Frontend Implementation

The frontend page (`MultipleChoicePage.tsx`) should:
- Display questions one at a time or all at once
- Show progress (Question X of Y)
- Allow selecting answers (radio buttons or clickable cards)
- Provide immediate feedback on selection
- Show explanation after answering
- Calculate and display final score

## Best Practices

1. **Generate diverse questions**: Cover different aspects of each topic
2. **Use clear language**: Questions should be unambiguous
3. **Create plausible distractors**: Wrong answers should be believable
4. **Include explanations**: Help users learn from mistakes
5. **Tag appropriately**: Use tags for better filtering and organization

## Next Steps

1. Create `MultipleChoicePage.tsx` frontend component
2. Update `GameSessionPage.tsx` to route multiple_choice games
3. Add visual enhancements (animations, progress bars)
4. Implement question review mode after completion

