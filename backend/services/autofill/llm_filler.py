"""
LLM-based field filler for complex form questions.
Uses Ollama or OpenRouter to infer answers from CV and memory.
"""
from typing import Dict, Any, Optional, List
import json
import importlib.util
from pathlib import Path


PROMPT_TEMPLATE = """You are helping fill a job application form. Analyze the form field and provide the best answer based on the user's CV and previous answers.

USER'S CV:
{cv_data}

PREVIOUS ANSWERS FOR THIS COMPANY:
{company_memory}

PREVIOUS GLOBAL ANSWERS:
{global_memory}

FORM FIELD TO FILL:
Label: "{field_label}"
Type: {field_type}
Placeholder: "{placeholder}"
{options_text}

TASK: Provide the best answer for this field.

IMPORTANT RULES:
1. Use CV data when directly relevant
2. Check previous answers for similar questions  
3. For yes/no questions, return ONLY "Yes" or "No"
4. For number fields, return ONLY the number
5. For dates, use format shown in placeholder or YYYY-MM-DD
6. If unsure or need user verification, set confidence < 0.7
7. For select/radio, choose from the provided options
8. Be concise - match the expected format

Return ONLY valid JSON in this exact format:
{{"answer": "your answer here", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""


def format_cv_summary(cv_data: Dict[str, Any]) -> str:
    """Format CV data into readable text for the prompt"""
    if not cv_data:
        return "No CV data available."
    
    summary_parts = []
    
    # Personal info
    personal = cv_data.get('personal_info', {})
    if personal:
        summary_parts.append(f"Name: {personal.get('first_name', '')} {personal.get('last_name', '')}")
        summary_parts.append(f"Email: {personal.get('email', '')}")
        summary_parts.append(f"Phone: {personal.get('phone', '')}")
        summary_parts.append(f"Location: {personal.get('location', '')}")
    
    # Work experience
    work_exp = cv_data.get('work_experience', [])
    if work_exp:
        summary_parts.append("\nWork Experience:")
        for i, exp in enumerate(work_exp[:3], 1):  # Top 3
            summary_parts.append(
                f"{i}. {exp.get('job_title', '')} at {exp.get('company', '')} "
                f"({exp.get('start_date', '')} - {exp.get('end_date', '')})"
            )
    
    # Education
    education = cv_data.get('education', [])
    if education:
        summary_parts.append("\nEducation:")
        for i, edu in enumerate(education, 1):
            summary_parts.append(
                f"{i}. {edu.get('degree', '')} in {edu.get('field_of_study', '')} "
                f"from {edu.get('institution', '')} ({edu.get('graduation_year', '')})"
            )
    
    # Skills
    skills = cv_data.get('skills', {})
    if skills:
        technical = skills.get('technical', [])
        if technical:
            summary_parts.append(f"\nTechnical Skills: {', '.join(technical[:15])}")
    
    return '\n'.join(summary_parts)


def format_memory(memories: List[Dict[str, Any]]) -> str:
    """Format memory entries into readable text"""
    if not memories:
        return "None"
    
    lines = []
    for mem in memories[:10]:  # Top 10 most recent
        lines.append(f"Q: {mem.get('question_text', '')}")
        lines.append(f"A: {mem.get('answer_text', '')}")
        lines.append("")
    
    return '\n'.join(lines)


async def analyze_field_with_llm(
    field_label: str,
    field_type: str,
    placeholder: Optional[str],
    options: Optional[List[str]],
    cv_data: Dict[str, Any],
    company_memory: List[Dict[str, Any]],
    global_memory: List[Dict[str, Any]],
    llm_service  # LLMService instance (no type hint due to dynamic import)
) -> Dict[str, Any]:
    """
    Use LLM to analyze a form field and suggest an answer.
    Returns: {answer, confidence, reasoning}
    """
    # Build options text
    options_text = ""
    if options and len(options) > 0:
        options_text = f"Options: {', '.join(options)}"
    
    # Build prompt
    prompt = PROMPT_TEMPLATE.format(
        cv_data=format_cv_summary(cv_data),
        company_memory=format_memory(company_memory),
        global_memory=format_memory(global_memory),
        field_label=field_label,
        field_type=field_type,
        placeholder=placeholder or "None",
        options_text=options_text
    )
    
    try:
        # Call LLM
        response = await llm_service.generate_text(
            prompt=prompt,
            temperature=0.3,  # Low temperature for consistent answers
            max_tokens=200
        )
        
        # Parse JSON response
        response_text = response.strip()
        
        # Try to extract JSON if wrapped in markdown
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        result = json.loads(response_text)
        
        # Validate structure
        if 'answer' not in result or 'confidence' not in result:
            raise ValueError("Invalid response structure")
        
        # Ensure confidence is a float between 0 and 1
        confidence = float(result.get('confidence', 0.5))
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            'answer': str(result.get('answer', '')),
            'confidence': confidence,
            'reasoning': str(result.get('reasoning', ''))
        }
    
    except Exception as e:
        # Fallback on error
        return {
            'answer': '',
            'confidence': 0.0,
            'reasoning': f'LLM analysis failed: {str(e)}'
        }

