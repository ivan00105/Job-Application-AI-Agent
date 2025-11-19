"""
LLM-based form filler that analyzes HTML and provides action instructions.
Single LLM call handles both structure understanding and value filling.
"""
from typing import Dict, Any, List
import json
import re
from pathlib import Path
from .fuzzy_matcher import fuzzy_match_field_label


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
    # Combine memory (company memory takes priority)
    all_memory = company_memory + global_memory
    element_lookup = {el.get('id'): el for el in elements if el.get('id')}
    
    # PRE-FILL STEP: Use fuzzy matching to auto-fill fields with saved answers (80%+ similarity)
    prefilled_actions = []
    elements_needing_llm = []
    
    for element in elements:
        field_label = element.get('label', '')
        
        # Try fuzzy match with memory (80% similarity threshold)
        matched_memory = fuzzy_match_field_label(field_label, all_memory, threshold=0.8)
        
        if matched_memory:
            # Auto-fill with high confidence (memory match)
            answer = matched_memory.get('answer_text', '')
            # Skip if answer is empty, "None", or other placeholder values
            if answer and answer.lower() not in ['none', 'n/a', 'null', 'not applicable', '']:
                # Determine interaction type based on role
                role = element.get('role', '')
                interaction = 'fill_text'  # default
                if role in ['combobox', 'listbox']:
                    interaction = 'select_option'
                elif role in ['checkbox', 'switch']:
                    interaction = 'check'
                elif role in ['button', 'radio', 'option']:
                    interaction = 'click'
                
                prefilled_actions.append({
                    'label': field_label,
                    'elementId': element.get('id', ''),
                    'interaction': interaction,
                    'value': answer,
                    'confidence': 'high',
                    'reasoning': f"Found in memory (fuzzy match with '{matched_memory['question_text']}')"
                })
                print(f"[Pre-fill] Auto-filled '{field_label}' with saved answer: '{answer}'")
                continue  # Skip LLM for this field
        
        # No memory match - needs LLM analysis
        elements_needing_llm.append(element)
    
    print(f"[LLM Form Filler] Pre-filled {len(prefilled_actions)} fields from memory")
    print(f"[LLM Form Filler] {len(elements_needing_llm)} fields need LLM analysis")
    
    # If all fields were pre-filled, skip LLM call entirely!
    if len(elements_needing_llm) == 0:
        print(f"[LLM Form Filler] All fields pre-filled from memory. Skipping LLM call!")
        return prefilled_actions
    
    # Load prompt template
    prompt_template = load_prompt_template()
    
    # Format ONLY elements needing LLM analysis (reduces token usage)
    elements_summary = format_elements_list(elements_needing_llm)
    
    # Build prompt with structured elements
    prompt = prompt_template.format(
        cv_data=format_cv_summary(cv_data),
        memory_data=format_memory(all_memory),
        form_elements=elements_summary  # Only unfilled elements
    )
    
    # Debug logging
    print(f"[LLM Form Filler] Sending {len(elements_needing_llm)} elements to LLM")
    print(f"[LLM Form Filler] Prompt size: {len(prompt)} characters")
    
    try:
        # Call LLM - only for fields not pre-filled
        response = await llm_service.generate_text(
            prompt=prompt,
            temperature=0.1,  # Very low temperature for aggressive high confidence
            max_tokens=8000  # Large response for complete JSON with many fields
        )
        
        # Parse JSON response
        llm_actions = parse_llm_response(response)
        llm_actions = filter_valid_actions(llm_actions, element_lookup)
        
        # Combine pre-filled actions with LLM actions
        all_actions = prefilled_actions + llm_actions
        
        print(f"[LLM Form Filler] Parsed {len(llm_actions)} actions from LLM response")
        print(f"[LLM Form Filler] Total actions (pre-filled + LLM): {len(all_actions)}")
        return all_actions
    
    except Exception as e:
        print(f"[LLM Form Filler] Error: {str(e)}")
        # Return pre-filled actions even if LLM fails
        print(f"[LLM Form Filler] Returning {len(prefilled_actions)} pre-filled actions despite error")
        return prefilled_actions


def format_elements_list(elements: List[Dict]) -> str:
    """Format A11y elements for LLM."""
    lines = []
    for el in elements:
        lines.append(f"ID: {el['id']}")
        lines.append(f"  Role: {el['role']}")
        lines.append(f"  Label: {el['label']}")
        if el.get('type'):
            lines.append(f"  Type: {el['type']}")
        if el.get('required'):
            lines.append(f"  Required: yes")
        if el.get('currentValue'):
            lines.append(f"  Current: {el['currentValue']}")
        if el.get('description'):
            lines.append(f"  Description: {el['description']}")
        if el.get('context'):
            lines.append(f"  Context: {el['context']}")
        lines.append("")
    
    return "\n".join(lines)


def filter_valid_actions(actions: List[Dict[str, Any]], element_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure actions reference known elements and valid interactions."""
    role_interaction_map = {
        'textbox': {'fill_text'},
        'searchbox': {'fill_text'},
        'spinbutton': {'fill_text'},
        'textarea': {'fill_text'},
        'combobox': {'select_option', 'fill_text', 'click', 'need_options'},
        'listbox': {'select_option', 'click', 'need_options'},
        'checkbox': {'check'},
        'switch': {'check'},
        'radio': {'click'},
        'button': {'click'},
        'option': {'click'},
    }

    valid_actions = []
    for action in actions:
        element = element_lookup.get(action['elementId'])
        if not element:
            print(f"[LLM Form Filler] Dropping action for unknown elementId: {action['elementId']}")
            continue

        role = (element.get('role') or '').lower()
        allowed_interactions = role_interaction_map.get(role)
        if allowed_interactions and action['interaction'] not in allowed_interactions:
            print(f"[LLM Form Filler] Dropping action with invalid interaction '{action['interaction']}' for role '{role}'")
            continue

        valid_actions.append(action)

    return valid_actions


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
        
        # Required fields (NEW: elementId instead of selector)
        if 'label' not in action or 'elementId' not in action or 'interaction' not in action:
            print(f"[LLM Form Filler] Skipping action missing required fields: {action}")
            continue
        
        # Clean value
        value = str(action.get('value', ''))
        if value.lower() in ['none', 'n/a', 'null', 'not applicable']:
            value = ''
        
        # Validate interaction type (including "need_options" for Pass 1)
        interaction = action.get('interaction', '')
        if interaction not in ['fill_text', 'click', 'select_option', 'check', 'need_options']:
            print(f"[LLM Form Filler] Invalid interaction type: {interaction}")
            continue
        
        # Validate confidence
        confidence = action.get('confidence', 'low')
        if confidence not in ['high', 'medium', 'low']:
            confidence = 'low'
        
        cleaned_actions.append({
            'label': action.get('label', ''),
            'elementId': action.get('elementId', ''),  # NEW: Use elementId
            'interaction': interaction,
            'value': value,
            'confidence': confidence,
            'reasoning': action.get('reasoning', '')
        })
    
    return cleaned_actions

