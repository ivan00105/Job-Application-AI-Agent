"""
Profile scoring service - Analyzes user CV profile and generates scores for radar diagram.
Uses AI to evaluate 6 dimensions: Qualification, Experience, Technical Skills, Soft Skills, Tools & Platforms, Industry Knowledge.
"""
import json
import httpx
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Import LLM logger with fallback
try:
    from backend.services.shared.llm_logger import log_llm_call
except ImportError:
    try:
        from services.shared.llm_logger import log_llm_call
    except ImportError:
        # Fallback if logger not available
        def log_llm_call(*args, **kwargs):
            pass


class ProfileScoringService:
    """Service for AI-powered profile scoring and analysis"""

    def __init__(self):
        self.openrouter_api_key = settings.openrouter_api_key
        self.openrouter_base_url = settings.openrouter_base_url or "https://openrouter.ai/api/v1"
        self.openrouter_model = settings.openrouter_model or "openrouter/gpt-oss-120b"

    async def _call_openrouter(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[str] = None
    ) -> str:
        """Call OpenRouter API"""
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")

        json_data = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "system", "content": system_prompt} if system_prompt else {"role": "system", "content": "You are an expert career advisor and resume analyst."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format:
            json_data["response_format"] = {"type": response_format}

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "HTTP-Referer": getattr(settings, 'openrouter_http_referer', None) or "https://github.com/your-repo",
                        "X-Title": "Job Application AI Agent"
                    },
                    json=json_data
                )
                response.raise_for_status()
                data = response.json()
                
                duration_ms = (time.time() - start_time) * 1000
                generated_text = data["choices"][0]["message"]["content"].strip()
                
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")
                
                log_llm_call(
                    provider="openrouter",
                    model=self.openrouter_model,
                    prompt=prompt[:500],
                    system_prompt=system_prompt[:200] if system_prompt else None,
                    response=generated_text[:500],
                    request_data=json_data,
                    response_data={"usage": usage},
                    duration_ms=duration_ms,
                    tokens_used=tokens_used,
                    metadata={"function": "profile_scoring"}
                )
                
                return generated_text
                
        except httpx.HTTPError as e:
            logger.error(f"OpenRouter API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling OpenRouter: {str(e)}")
            raise

    def _calculate_basic_metrics(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic quantitative metrics from parsed CV data"""
        metrics = {
            "qualification_score": 0,
            "experience_years": 0,
            "technical_skills_count": 0,
            "soft_skills_count": 0,
            "tools_count": 0,
            "certifications_count": 0,
            "education_level": "none"
        }

        # Count certifications
        certifications = parsed_data.get("certifications", [])
        if isinstance(certifications, list):
            metrics["certifications_count"] = len(certifications)

        # Count education and determine level
        education = parsed_data.get("education", [])
        if isinstance(education, list) and education:
            metrics["certifications_count"] += len(education)
            # Determine highest education level
            degrees = [e.get("degree", "").lower() for e in education if isinstance(e, dict)]
            if any("phd" in d or "doctorate" in d for d in degrees):
                metrics["education_level"] = "phd"
            elif any("master" in d or "ms" in d or "mba" in d for d in degrees):
                metrics["education_level"] = "masters"
            elif any("bachelor" in d or "bs" in d or "ba" in d for d in degrees):
                metrics["education_level"] = "bachelors"
            elif any("associate" in d or "diploma" in d for d in degrees):
                metrics["education_level"] = "associate"

        # Calculate experience years
        work_experience = parsed_data.get("work_experience", [])
        if isinstance(work_experience, list):
            total_months = 0
            for exp in work_experience:
                if not isinstance(exp, dict):
                    continue
                start_date = exp.get("start_date", "")
                end_date = exp.get("end_date", "Present")
                
                # Simple date parsing (YYYY-MM or MM/YYYY)
                try:
                    if start_date:
                        if "/" in start_date:
                            parts = start_date.split("/")
                            start_year = int(parts[1] if len(parts) > 1 else parts[0])
                        else:
                            start_year = int(start_date.split("-")[0])
                        
                        if end_date and end_date.lower() != "present":
                            if "/" in end_date:
                                parts = end_date.split("/")
                                end_year = int(parts[1] if len(parts) > 1 else parts[0])
                            else:
                                end_year = int(end_date.split("-")[0])
                        else:
                            end_year = datetime.now().year
                        
                        total_months += (end_year - start_year) * 12
                except (ValueError, IndexError):
                    pass
            
            metrics["experience_years"] = round(total_months / 12, 1)

        # Count skills
        skills = parsed_data.get("skills", {})
        if isinstance(skills, dict):
            metrics["technical_skills_count"] = len(skills.get("technical", []))
            metrics["soft_skills_count"] = len(skills.get("soft", []))
            metrics["tools_count"] = len(skills.get("tools", []))

        # Also check projects for technologies
        projects = parsed_data.get("projects", [])
        if isinstance(projects, list):
            for project in projects:
                if isinstance(project, dict):
                    techs = project.get("technologies", [])
                    if isinstance(techs, list):
                        metrics["tools_count"] += len(techs)

        return metrics

    async def analyze_profile(
        self,
        parsed_data: Dict[str, Any],
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze user profile and generate scores for 6 dimensions.
        Returns scores (0-100) and recommendations.
        """
        # Calculate basic metrics
        basic_metrics = self._calculate_basic_metrics(parsed_data)

        # Prepare CV summary for AI analysis
        cv_summary_parts = []
        
        # Education summary
        education = parsed_data.get("education", [])
        if education:
            edu_list = []
            for edu in education[:3]:  # Top 3
                if isinstance(edu, dict):
                    degree = edu.get("degree", "")
                    institution = edu.get("institution", "")
                    if degree:
                        edu_list.append(f"{degree} from {institution}" if institution else degree)
            if edu_list:
                cv_summary_parts.append(f"Education: {', '.join(edu_list)}")

        # Certifications
        certifications = parsed_data.get("certifications", [])
        if certifications:
            cert_names = [c.get("name", "") if isinstance(c, dict) else str(c) for c in certifications[:5]]
            cert_names = [c for c in cert_names if c]
            if cert_names:
                cv_summary_parts.append(f"Certifications: {', '.join(cert_names)}")

        # Experience summary
        work_experience = parsed_data.get("work_experience", [])
        if work_experience:
            exp_list = []
            for exp in work_experience[:3]:  # Top 3
                if isinstance(exp, dict):
                    title = exp.get("job_title", "")
                    company = exp.get("company", "")
                    if title:
                        exp_list.append(f"{title} at {company}" if company else title)
            if exp_list:
                cv_summary_parts.append(f"Work Experience: {', '.join(exp_list)}")
        
        cv_summary_parts.append(f"Total Experience: {basic_metrics['experience_years']} years")

        # Skills summary
        skills = parsed_data.get("skills", {})
        if isinstance(skills, dict):
            technical = skills.get("technical", [])[:10]
            soft = skills.get("soft", [])[:10]
            tools = skills.get("tools", [])[:10]
            
            if technical:
                cv_summary_parts.append(f"Technical Skills: {', '.join(technical)}")
            if soft:
                cv_summary_parts.append(f"Soft Skills: {', '.join(soft)}")
            if tools:
                cv_summary_parts.append(f"Tools & Platforms: {', '.join(tools)}")

        # Projects
        projects = parsed_data.get("projects", [])
        if projects:
            project_techs = []
            for project in projects[:3]:
                if isinstance(project, dict):
                    techs = project.get("technologies", [])
                    if isinstance(techs, list):
                        project_techs.extend(techs)
            if project_techs:
                cv_summary_parts.append(f"Project Technologies: {', '.join(set(project_techs))}")

        cv_summary = "\n".join(cv_summary_parts)

        # AI prompt for scoring
        system_prompt = """You are an expert career advisor analyzing a candidate's profile. 
Evaluate the profile across 6 dimensions and provide scores (0-100) and recommendations.
Consider market standards and competitiveness."""

        user_prompt = f"""Analyze this CV profile and provide scores for 6 dimensions:

CV Summary:
{cv_summary}

Basic Metrics:
- Education Level: {basic_metrics['education_level']}
- Certifications: {basic_metrics['certifications_count']}
- Experience: {basic_metrics['experience_years']} years
- Technical Skills: {basic_metrics['technical_skills_count']}
- Soft Skills: {basic_metrics['soft_skills_count']}
- Tools: {basic_metrics['tools_count']}

Evaluate each dimension (0-100 scale):
1. **Qualification**: Education level, degrees, certifications, academic achievements
2. **Experience**: Years of relevant experience, career progression, role seniority
3. **Technical Skills**: Depth and breadth of technical skills, relevance to market
4. **Soft Skills**: Communication, leadership, teamwork, problem-solving abilities
5. **Tools & Platforms**: Familiarity with industry tools, platforms, technologies
6. **Industry Knowledge**: Domain expertise, industry-specific knowledge, market understanding

Return ONLY valid JSON in this format:
{{
  "scores": {{
    "qualification": 75,
    "experience": 80,
    "technical_skills": 70,
    "soft_skills": 65,
    "tools_platforms": 72,
    "industry_knowledge": 68
  }},
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "recommendations": [
    {{"dimension": "qualification", "action": "specific recommendation"}},
    {{"dimension": "experience", "action": "specific recommendation"}}
  ],
  "competitor_insights": {{
    "common_qualifications": ["qualification 1", "qualification 2"],
    "enhancement_suggestions": ["suggestion 1", "suggestion 2"]
  }}
}}"""

        try:
            response_text = await self._call_openrouter(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2000,
                response_format="json_object"
            )

            # Parse JSON response
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                    analysis = json.loads(response_text)
                else:
                    raise ValueError("Invalid JSON response from AI")

            # Ensure scores are in the expected format
            scores = analysis.get("scores", {})
            default_scores = {
                "qualification": 50,
                "experience": 50,
                "technical_skills": 50,
                "soft_skills": 50,
                "tools_platforms": 50,
                "industry_knowledge": 50
            }

            for key in default_scores:
                if key not in scores:
                    scores[key] = default_scores[key]
                # Ensure scores are between 0-100
                scores[key] = max(0, min(100, float(scores.get(key, 50))))

            analysis["scores"] = scores
            analysis["basic_metrics"] = basic_metrics

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing profile: {str(e)}")
            # Return default scores on error
            return {
                "scores": {
                    "qualification": 50,
                    "experience": 50,
                    "technical_skills": 50,
                    "soft_skills": 50,
                    "tools_platforms": 50,
                    "industry_knowledge": 50
                },
                "strengths": [],
                "weaknesses": ["Unable to analyze profile. Please ensure your CV is complete."],
                "recommendations": [],
                "competitor_insights": {
                    "common_qualifications": [],
                    "enhancement_suggestions": []
                },
                "basic_metrics": basic_metrics,
                "error": str(e)
            }

