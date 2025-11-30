# Algorithm Puzzles Implementation

## Overview

Algorithm puzzles are now fully implemented in the Challenge Center! Users can solve coding challenges, run their code against test cases, and get instant feedback.

## What's Been Implemented

### Backend

1. **Code Executor** (`backend/services/games/code_executor.py`)
   - Executes Python code safely with timeout protection
   - Runs code against test cases
   - Handles both return values and in-place modifications
   - Provides detailed test results

2. **Coding Game Handler** (`backend/services/games/coding_handler.py`)
   - Validates coding challenge content
   - Evaluates user submissions
   - Calculates scores based on test results
   - Generates feedback messages

3. **API Endpoints**
   - `GET /api/games/sessions/{session_id}` - Get session with game details
   - `POST /api/games/sessions/{session_id}/submit` - Submit code solution
   - `POST /api/games/sessions/{session_id}/complete` - Complete challenge

### Frontend

1. **Code Editor Component** (`src/components/CodeEditor.tsx`)
   - Syntax-highlighted code editor
   - Run tests button
   - Reset to starter code
   - Language indicator

2. **Coding Challenge Page** (`src/pages/CodingChallengePage.tsx`)
   - Problem description display
   - Code editor with test runner
   - Real-time test results
   - Timer display
   - Complete challenge button

3. **Sample Puzzles** (`backend/scripts/seed/seed_algorithm_puzzles.py`)
   - 5 algorithm puzzles ready to use:
     - Two Sum (Beginner)
     - Reverse String (Beginner)
     - Valid Parentheses (Intermediate)
     - Maximum Subarray (Intermediate)
     - Binary Search (Intermediate)

## Setup Instructions

### 1. Run Database Migration (if not done)

```bash
cd backend
python scripts/run_game_library_migration.py
```

### 2. Seed Algorithm Puzzles

```bash
cd backend
python scripts/seed/seed_algorithm_puzzles.py
```

This will add 5 sample algorithm puzzles to your database.

### 3. Start Backend

```bash
cd backend
python main.py
```

### 4. Start Frontend

```bash
npm run dev
```

## How It Works

1. **User starts a challenge** from the Challenge Center
2. **Problem is displayed** with description, examples, and function signature
3. **User writes code** in the code editor
4. **User clicks "Run Tests"** to submit code
5. **Backend executes code** against all test cases
6. **Results are displayed** showing which tests passed/failed
7. **User can iterate** and resubmit until all tests pass
8. **User completes challenge** when satisfied

## Code Execution Details

- **Language**: Currently supports Python 3
- **Timeout**: 10 seconds per test case
- **Security**: Code runs in subprocess with timeout protection
- **Test Cases**: Each puzzle has 3-5 test cases

## Adding New Puzzles

Edit `backend/scripts/seed/seed_algorithm_puzzles.py` and add a new puzzle to the `ALGORITHM_PUZZLES` list:

```python
{
    "title": "Your Puzzle Title",
    "description": "Problem description...",
    "game_type": "coding",
    "domain": "IT",
    "difficulty": "beginner",  # or "intermediate", "advanced"
    "points": 100,
    "time_limit_minutes": 15,
    "tags": ["array", "hash-table"],
    "game_content": {
        "description": "Short description",
        "language": "python",
        "function_signature": "def your_function(params):",
        "starter_code": "def your_function(params):\n    # Your code here\n    pass",
        "test_cases": [
            {
                "name": "Test 1",
                "input": {"param1": value1, "param2": value2},
                "expected_output": expected_result
            }
        ]
    }
}
```

Then run the seed script again.

## Test Case Format

Test cases support:
- **Named parameters**: `{"input": {"nums": [1,2,3], "target": 5}}`
- **Positional arguments**: `{"input": [1, 2, 3]}`
- **Single argument**: `{"input": "hello"}`

Expected output can be:
- Any JSON-serializable value
- Lists/arrays are compared element-wise
- Floats allow small differences (1e-9)

## Future Enhancements

- [ ] JavaScript support
- [ ] Code syntax highlighting (Monaco Editor)
- [ ] Auto-completion
- [ ] Code templates/snippets
- [ ] Performance metrics (execution time)
- [ ] Code quality analysis
- [ ] Hints system
- [ ] Solution explanations
- [ ] Leaderboards per puzzle
- [ ] Difficulty progression

## Security Considerations

Current implementation:
- ✅ Timeout protection (10 seconds)
- ✅ Subprocess isolation
- ⚠️ Not fully sandboxed (runs on server)

For production, consider:
- Docker containers for code execution
- Resource limits (CPU, memory)
- Network restrictions
- File system restrictions
- Restricted Python modules

## Troubleshooting

**Code execution fails:**
- Check that Python 3 is installed: `python3 --version`
- Check backend logs for error messages
- Verify test case format is correct

**Tests not passing:**
- Check function signature matches
- Verify return type matches expected output
- Check for edge cases

**Frontend not loading:**
- Verify API endpoint is accessible
- Check browser console for errors
- Ensure session ID is valid

