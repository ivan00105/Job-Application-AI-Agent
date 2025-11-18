# Agentic CV Generation System

## Overview

The agentic CV generation system uses multi-step reasoning and autonomous decision-making to create tailored CVs. Instead of a single-step generation process, the AI agent breaks down the task into multiple reasoning steps, making intelligent decisions at each stage.

## Architecture

### Agentic Workflow

The agent follows a 6-step process:

1. **Analyze Job** 🤖
   - Extracts key requirements from job description
   - Identifies required skills, qualifications, and responsibilities
   - Determines what the employer values most

2. **Analyze CV** 🤖
   - Matches CV content to job requirements
   - Identifies relevant experiences and skills
   - Finds strengths and potential gaps

3. **Create Strategy** 🤖
   - Develops a tailoring strategy based on analysis
   - Decides content priorities and structure
   - Determines customization approach

4. **Generate Content** 🤖
   - Creates HTML CV following the strategy
   - Integrates keywords naturally
   - Applies formatting and structure decisions

5. **Validate Output** 🤖
   - Checks if CV meets requirements
   - Validates HTML structure
   - Assesses quality and completeness

6. **Refine Output** 🤖 (iterative, up to 5 rounds)
   - Fixes identified issues
   - Re-validates after each refinement
   - Continues until no issues remain or max rounds reached
   - Tracks improvement across rounds

## Key Features

### Autonomous Decision-Making

The agent makes decisions at each step:
- **What to emphasize**: Based on job analysis, decides which experiences/skills to highlight
- **How to structure**: Determines section order and space allocation
- **Content priorities**: Decides what content is most important for this specific job
- **Quality assessment**: Evaluates its own output and decides if refinement is needed

### Multi-Step Reasoning

Each step builds on the previous:
- Job analysis informs CV analysis
- Both analyses inform strategy creation
- Strategy guides content generation
- Validation provides feedback for refinement

### Iterative Refinement (Up to 5 Rounds)

The agent can refine its output multiple times:
- Validates quality (score 1-10)
- Identifies specific issues (critical and minor)
- Automatically refines if issues found
- Re-validates after each refinement round
- Continues until:
  - ✅ No issues remain
  - ✅ Quality score ≥ 8 and no issues
  - ✅ No new issues found (same issues as previous round)
  - ⚠️ Maximum 5 rounds reached
- Tracks improvement: shows quality score and issue count changes

## Configuration

### Enable/Disable Agentic Mode

In `backend/config.py` or `.env`:

```python
use_agentic_cv_generation: bool = True  # Default: True
```

Or in `.env`:
```bash
USE_AGENTIC_CV_GENERATION=true
```

### Fallback to Traditional Mode

If agentic generation fails or is disabled, the system automatically falls back to the traditional single-step generation method.

## Benefits

### 1. Better Quality
- More thoughtful analysis of job requirements
- Strategic approach to tailoring
- Self-validation and refinement

### 2. More Relevant CVs
- Deep understanding of job requirements
- Better matching of CV content to job needs
- Strategic keyword integration

### 3. Autonomous Operation
- Agent makes decisions without human intervention
- Handles complex scenarios automatically
- Adapts approach based on analysis

### 4. Transparency
- Returns agent analysis and strategy
- Shows reasoning steps
- Provides validation feedback

## API Response

The agentic service returns additional information:

```json
{
  "html_content": "...",
  "emphasis_notes": "...",
  "success": true,
  "agent_steps": [
    {
      "step": "analyze_job",
      "success": true,
      "analysis": {...}
    },
    ...
  ],
  "agent_analysis": {
    "job_analysis": {...},
    "cv_analysis": {...},
    "strategy": {...},
    "validation": {...}
  }
}
```

## Usage

The agentic service is automatically used when `use_agentic_cv_generation` is enabled. No code changes needed - it's a drop-in replacement for the traditional service.

### Example

```python
from services.cv.agentic_cv_service import get_agentic_cv_service

service = get_agentic_cv_service()
result = await service.generate_tailored_cv_html(
    cv_parsed_data=cv_data,
    job_description=job_desc,
    job_title="Software Engineer",
    company="Tech Corp"
)

if result["success"]:
    html = result["html_content"]
    analysis = result["agent_analysis"]  # See agent's reasoning
    steps = result["agent_steps"]  # See all steps taken
```

## Performance

- **Time**: Longer than traditional (6 steps + up to 5 refinement rounds)
- **Quality**: Significantly better relevance and tailoring
- **Refinement**: Automatically refines up to 5 rounds until no issues remain
- **Cost**: More LLM calls, but better results justify the cost
- **Stopping Conditions**: Stops early if quality is excellent or no issues found

## Future Enhancements

1. **Parallel Processing**: Run some steps in parallel
2. **Caching**: Cache job analysis for similar jobs
3. **Learning**: Learn from user feedback to improve strategy
4. **Multi-Agent**: Specialized agents for different sections
5. **Real-time Progress**: Stream agent steps to frontend

## Troubleshooting

### Agent fails at analysis step
- Check LLM API key and connectivity
- Verify job description is not empty
- Check CV data is properly formatted

### Quality score is low
- Agent will automatically refine
- Check validation issues in response
- May need better CV data or job description

### Want to disable agentic mode
- Set `USE_AGENTIC_CV_GENERATION=false` in `.env`
- System will use traditional single-step generation

