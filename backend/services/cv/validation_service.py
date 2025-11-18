"""
CV Validation Service
Validates edited CV content without full regeneration.
"""
import os
import sys
import re
from typing import Dict, Any, Optional

from config import get_settings

# Import LLM service
services_path = os.path.join(os.path.dirname(__file__), '..', 'jobs-finder')
sys.path.insert(0, services_path)
from llm_service import llm_service


class CVValidationService:
    """Service for validating CV content"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def validate_edited_cv(
        self,
        html_content: str,
        original_cv_text: str,
        job_description: Optional[str] = None,
        job_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate edited CV content.
        
        Args:
            html_content: Edited HTML CV content
            original_cv_text: Original CV text for reference
            job_description: Optional job description
            job_analysis: Optional job analysis from agent
            
        Returns:
            Validation result dictionary
        """
        # Extract text content from HTML
        text_content = re.sub(r'<[^>]+>', '', html_content)[:2000]
        
        system_prompt = """Validate CV quality. Return JSON with:
- is_valid_html: Boolean
- has_required_sections: Boolean (summary, experience, skills, education)
- style_acceptable: Boolean (professional styling, alignment, spacing)
- no_invented_content: Boolean (verify against original CV)
- issues: List of specific issues found
- critical_issues: Must fix issues
- minor_issues: Can improve issues
- quality_score: 1-10
- needs_refinement: Boolean
- recommendations: List of improvement recommendations

Return ONLY valid JSON."""
        
        user_prompt = f"""Validate this edited CV:

Original CV (for verification):
{original_cv_text[:1500]}

Edited CV (excerpt):
{text_content}

{f"Job description: {job_description[:500]}" if job_description else ""}

**CRITICAL**: Verify all content exists in original CV. Flag invented content.
**STYLE**: Check professional appearance, alignment, spacing, typography."""
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.2
            )
            
            # Parse JSON
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                validation = json.loads(json_match.group())
            else:
                # Fallback validation
                validation = self._basic_validation(html_content)
            
            return {
                "success": True,
                "validation": validation
            }
        except Exception as e:
            # Fallback validation
            return {
                "success": True,
                "validation": self._basic_validation(html_content),
                "warning": f"Full validation failed: {str(e)}"
            }
    
    def _basic_validation(self, html_content: str) -> Dict[str, Any]:
        """Basic validation without LLM"""
        is_valid = self._looks_like_html(html_content)
        has_sections = all(
            tag in html_content.lower() 
            for tag in ['summary', 'experience', 'skill']
        )
        
        return {
            "is_valid_html": is_valid,
            "has_required_sections": has_sections,
            "style_acceptable": True,
            "no_invented_content": True,
            "issues": [] if is_valid else ["HTML structure may be invalid"],
            "critical_issues": [] if is_valid else ["HTML structure may be invalid"],
            "minor_issues": [],
            "quality_score": 7 if is_valid and has_sections else 5,
            "needs_refinement": not (is_valid and has_sections),
            "recommendations": []
        }
    
    def _looks_like_html(self, text: str) -> bool:
        """Check if text looks like HTML"""
        if not text:
            return False
        text_lower = text.lstrip().lower()
        return text_lower.startswith("<!doctype") or "<html" in text_lower
    
    def validate_section_completeness(
        self,
        html_content: str
    ) -> Dict[str, Any]:
        """
        Check if all required sections are present.
        
        Args:
            html_content: HTML CV content
            
        Returns:
            Completeness check result
        """
        required_sections = {
            "summary": ["summary", "professional summary", "profile"],
            "experience": ["experience", "work", "employment", "career"],
            "skills": ["skill", "competenc", "expertise"],
            "education": ["education", "qualification", "degree"]
        }
        
        html_lower = html_content.lower()
        found_sections = {}
        
        for section_name, keywords in required_sections.items():
            found_sections[section_name] = any(
                keyword in html_lower for keyword in keywords
            )
        
        all_present = all(found_sections.values())
        missing = [name for name, found in found_sections.items() if not found]
        
        return {
            "all_sections_present": all_present,
            "found_sections": found_sections,
            "missing_sections": missing,
            "completeness_score": len(found_sections) - len(missing)
        }


# Singleton instance
_cv_validation_service = None

def get_cv_validation_service() -> CVValidationService:
    """Get singleton instance of CVValidationService"""
    global _cv_validation_service
    if _cv_validation_service is None:
        _cv_validation_service = CVValidationService()
    return _cv_validation_service

