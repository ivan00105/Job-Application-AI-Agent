"""
LLM-based form filler that analyzes HTML and provides action instructions.
Single LLM call handles both structure understanding and value filling.
"""
from typing import Dict, Any, List
import json
import re
from pathlib import Path


def load_prompt_template() -> str:
    """Load prompt template from file"""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "form_fill_prompt.txt"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def format_cv_summary(cv_data: Dict[str, Any]) -> str:
    """Format CV data into readable text for the prompt"""
    if not cv_data:
        return "No CV data available."
    
    summary_parts = []
    
    # Personal info
    personal = cv_data.get('personal_info', {})
    if personal:
        summary_parts.append("PERSONAL INFO:")
        if personal.get('full_name'):
            summary_parts.append(f"  Full Name: {personal.get('full_name')}")
        if personal.get('first_name'):
            summary_parts.append(f"  First Name: {personal.get('first_name')}")
        if personal.get('last_name'):
            summary_parts.append(f"  Last Name: {personal.get('last_name')}")
        if personal.get('email'):
            summary_parts.append(f"  Email: {personal.get('email')}")
        if personal.get('phone'):
            summary_parts.append(f"  Phone: {personal.get('phone')}")
        if personal.get('location'):
            summary_parts.append(f"  Location: {personal.get('location')}")
        if personal.get('linkedin'):
            summary_parts.append(f"  LinkedIn: {personal.get('linkedin')}")
        if personal.get('github'):
            summary_parts.append(f"  GitHub: {personal.get('github')}")
    
    # Work experience
    work_exp = cv_data.get('work_experience', [])
    if work_exp:
        summary_parts.append("\nWORK EXPERIENCE:")
        for i, exp in enumerate(work_exp[:5], 1):  # Top 5
            summary_parts.append(
                f"  {i}. {exp.get('job_title', '')} at {exp.get('company', '')}"
            )
            summary_parts.append(
                f"     Duration: {exp.get('start_date', '')} - {exp.get('end_date', 'Present')}"
            )
            if exp.get('description'):
                summary_parts.append(f"     Description: {exp.get('description', '')[:200]}")
    
    # Education
    education = cv_data.get('education', [])
    if education:
        summary_parts.append("\nEDUCATION:")
        for i, edu in enumerate(education, 1):
            summary_parts.append(
                f"  {i}. {edu.get('degree', '')} in {edu.get('field_of_study', '')}"
            )
            summary_parts.append(
                f"     Institution: {edu.get('institution', '')} ({edu.get('graduation_year', '')})"
            )
    
    # Skills
    skills = cv_data.get('skills', {})
    if skills:
        technical = skills.get('technical', [])
        if technical:
            summary_parts.append(f"\nTECHNICAL SKILLS: {', '.join(technical[:15])}")
        
        soft = skills.get('soft', [])
        if soft:
            summary_parts.append(f"SOFT SKILLS: {', '.join(soft[:10])}")
    
    # Certifications
    certs = cv_data.get('certifications', [])
    if certs:
        summary_parts.append("\nCERTIFICATIONS:")
        for cert in certs[:5]:
            summary_parts.append(f"  - {cert.get('name', '')}")
    
    return '\n'.join(summary_parts)


def format_memory(memory_list: List[Dict[str, Any]]) -> str:
    """Format memory entries into readable text"""
    if not memory_list:
        return "No previous answers saved."
    
    lines = []
    for mem in memory_list[:20]:  # Top 20
        question = mem.get('question_text', '')
        answer = mem.get('answer_text', '')
        company = mem.get('company_name', '')
        
        if company:
            lines.append(f"[{company}] Q: {question} → A: {answer}")
        else:
            lines.append(f"Q: {question} → A: {answer}")
    
    return '\n'.join(lines)


async def analyze_and_fill_form(
    elements: List[Dict[str, Any]],  # NEW: structured element list
    cv_data: Dict[str, Any],
    company_memory: List[Dict[str, Any]],
    global_memory: List[Dict[str, Any]],
    llm_service  # LLMService instance (no type hint due to dynamic import)
) -> List[Dict[str, Any]]:
    """
    Analyze extracted form elements and generate fill actions.
    Much more efficient than full HTML parsing - no truncation needed!
    
    Returns list of actions:
    [{
        "label": "First Name",
        "selector": "#first-name",
        "interaction": "fill_text",
        "value": "John",
        "confidence": "high",
        "reasoning": "Found in CV"
    }]
    """
    # Load prompt template
    prompt_template = load_prompt_template()
    
    # Combine memory
    all_memory = company_memory + global_memory
    
    # Format elements for LLM (compact list)
    elements_summary = format_elements_list(elements)
    
    # Build prompt with structured elements
    prompt = prompt_template.format(
        cv_data=format_cv_summary(cv_data),
        memory_data=format_memory(all_memory),
        form_elements=elements_summary  # Compact list instead of huge HTML
    )
    
    # Debug logging
    print(f"[LLM Form Filler] Processing {len(elements)} form elements")
    print(f"[LLM Form Filler] Prompt size: {len(prompt)} characters")
    
    try:
        # Call LLM - now we have much more room for output
        response = await llm_service.generate_text(
            prompt=prompt,
            temperature=0.2,  # Low temperature for consistent, predictable output
            max_tokens=8000  # Large response for complete JSON with many fields
        )
        
        # Parse JSON response
        actions = parse_llm_response(response)
        
        print(f"[LLM Form Filler] Parsed {len(actions)} actions from LLM response")
        print(f"[LLM Form Filler] Actions: {[a['label'] for a in actions]}")
        return actions
    
    except Exception as e:
        print(f"[LLM Form Filler] Error: {str(e)}")
        # Return empty list on error - user will have to fill manually
        return []


def format_elements_list(elements: List[Dict]) -> str:
    """Format element list compactly for LLM."""
    lines = []
    for i, el in enumerate(elements):
        lines.append(f"{i+1}. {el['label']} ({el['type']})")
        lines.append(f"   - Selector: {el['selector']}")
        lines.append(f"   - Current value: {el.get('value', '')}")
        if el.get('placeholder'):
            lines.append(f"   - Placeholder: {el['placeholder']}")
        if el.get('required'):
            lines.append(f"   - Required: yes")
        if el.get('context'):
            lines.append(f"   - HTML context: {el['context'][:200]}")
        lines.append("")
    
    return "\n".join(lines)


def parse_llm_response(response: str) -> List[Dict[str, Any]]:
    """
    Parse LLM response to extract JSON array of actions.
    Handles markdown code blocks and other formatting.
    """
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
    
    # Find JSON array
    if not response_text.startswith('['):
        # Try to find the array in the text
        match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if match:
            response_text = match.group(0)
        else:
            raise ValueError("No JSON array found in LLM response")
    
    # Parse JSON
    try:
        actions = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"[LLM Form Filler] JSON parse error: {e}")
        print(f"[LLM Form Filler] Response text (first 1500 chars): {response_text[:1500]}")
        
        # Try to repair truncated JSON
        print(f"[LLM Form Filler] Attempting to repair truncated JSON...")
        repaired = response_text
        
        # If it's missing closing brackets, try to add them
        open_braces = repaired.count('{')
        close_braces = repaired.count('}')
        open_brackets = repaired.count('[')
        close_brackets = repaired.count(']')
        
        # Remove incomplete last object if present
        last_complete = repaired.rfind('}')
        if last_complete > 0:
            repaired = repaired[:last_complete + 1]
            
            # Add missing closing brackets
            if open_brackets > close_brackets:
                repaired += ']' * (open_brackets - close_brackets)
            
            try:
                actions = json.loads(repaired)
                print(f"[LLM Form Filler] ✓ Repaired JSON successfully! Recovered {len(actions)} actions")
            except json.JSONDecodeError:
                print(f"[LLM Form Filler] Failed to repair JSON")
                raise ValueError(f"Invalid JSON in LLM response: {str(e)}")
        else:
            raise ValueError(f"Invalid JSON in LLM response: {str(e)}")
    
    if not isinstance(actions, list):
        raise ValueError("LLM response is not a JSON array")
    
    # Validate and clean actions
    cleaned_actions = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        
        # Required fields
        if 'label' not in action or 'selector' not in action or 'interaction' not in action:
            print(f"[LLM Form Filler] Skipping action missing required fields: {action}")
            continue
        
        # Clean value
        value = str(action.get('value', ''))
        if value.lower() in ['none', 'n/a', 'null', 'not applicable']:
            value = ''
        
        # Validate interaction type
        interaction = action.get('interaction', '')
        if interaction not in ['fill_text', 'click', 'select_option', 'check']:
            print(f"[LLM Form Filler] Invalid interaction type: {interaction}")
            continue
        
        # Validate confidence
        confidence = action.get('confidence', 'low')
        if confidence not in ['high', 'medium', 'low']:
            confidence = 'low'
        
        cleaned_actions.append({
            'label': action.get('label', ''),
            'selector': action.get('selector', ''),
            'interaction': interaction,
            'value': value,
            'confidence': confidence,
            'reasoning': action.get('reasoning', '')
        })
    
    return cleaned_actions

