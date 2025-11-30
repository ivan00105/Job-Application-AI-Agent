# Question Generator Model Configuration

## Overview

The question generator system supports using a separate, more robust LLM model specifically for generating coding and multiple choice questions. This allows you to use a higher-quality model (like GPT-4 or Claude) for question generation while using a more cost-effective model for other tasks.

## Configuration

### Environment Variable

Add the following to your `.env` file:

```bash
# Optional: Use a separate, more robust model for question generation
# If not set, uses the default OPENROUTER_MODEL
OPENROUTER_QUESTION_GENERATOR_MODEL=openai/gpt-4
```

### Supported Models

You can use any model available on OpenRouter. Some recommended models for question generation:

**High Quality (Recommended for Production):**
- `openai/gpt-4` - GPT-4 for best quality
- `openai/gpt-4-turbo` - GPT-4 Turbo (faster, still high quality)
- `anthropic/claude-3-opus` - Claude 3 Opus (excellent reasoning)
- `anthropic/claude-3-sonnet` - Claude 3 Sonnet (good balance)

**Cost-Effective:**
- `openai/gpt-3.5-turbo` - GPT-3.5 Turbo (good quality, lower cost)
- `openrouter/gpt-oss-120b` - Open source model (default)

### Example Configuration

```bash
# Default model for general LLM tasks
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Robust model specifically for question generation
OPENROUTER_QUESTION_GENERATOR_MODEL=openai/gpt-4
```

## How It Works

1. **Default Behavior**: If `OPENROUTER_QUESTION_GENERATOR_MODEL` is not set, the system uses the default `OPENROUTER_MODEL` for all tasks, including question generation.

2. **Separate Model**: When `OPENROUTER_QUESTION_GENERATOR_MODEL` is set, both:
   - **Coding Question Generator** (`question_generator.py`)
   - **Multiple Choice Question Generator** (`multiple_choice_question_generator.py`)
   
   Will use the specified model instead of the default.

3. **Other Services**: All other LLM services (job search enhancement, CV generation, etc.) continue to use the default `OPENROUTER_MODEL`.

## Benefits

- **Higher Quality Questions**: Use GPT-4 or Claude for generating educational content
- **Cost Optimization**: Use cheaper models for routine tasks, premium models only for question generation
- **Flexibility**: Easily switch between models without code changes

## Usage

Once configured, question generation scripts will automatically use the specified model:

```bash
# Generate coding questions (uses OPENROUTER_QUESTION_GENERATOR_MODEL if set)
python backend/scripts/seed/seed_coding_questions.py

# Generate multiple choice questions (uses OPENROUTER_QUESTION_GENERATOR_MODEL if set)
python backend/scripts/generate_logic_questions.py
python backend/scripts/generate_cybersecurity_questions.py
```

## Verification

To verify the model is being used, check the LLM logs in `backend/logs/llm_calls/`. The logs will show which model was used for each question generation call.

