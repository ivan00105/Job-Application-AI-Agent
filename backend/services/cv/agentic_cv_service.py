"""
Agentic CV Generation Service
Uses multi-step reasoning and autonomous decision-making to generate tailored CVs.
The agent breaks down the task into: Analysis → Strategy → Generation → Validation → Refinement
"""
import os
import json
import re
import time
from typing import Dict, Any, Optional, List, AsyncGenerator
from enum import Enum

from config import get_settings

# Import LLM logger
try:
    from backend.services.shared.llm_logger import log_llm_call
except ImportError:
    try:
        from services.shared.llm_logger import log_llm_call
    except ImportError:
        def log_llm_call(*args, **kwargs):
            pass

# Import LLM service
import sys
services_path = os.path.join(os.path.dirname(__file__), '..', 'jobs-finder')
sys.path.insert(0, services_path)
from llm_service import llm_service

# Import CV HTML to PDF service
try:
    from backend.services.cv.cvhtml2pdf_service import get_cv_html2pdf_service
except ImportError:
    from services.cv.cvhtml2pdf_service import get_cv_html2pdf_service


class AgentStep(Enum):
    """Steps in the agentic CV generation process"""
    ANALYZE_JOB = "analyze_job"
    ANALYZE_CV = "analyze_cv"
    CREATE_STRATEGY = "create_strategy"
    GENERATE_CONTENT = "generate_content"
    VALIDATE_OUTPUT = "validate_output"
    REFINE_OUTPUT = "refine_output"


class AgenticCVService:
    """
    Agentic CV generation service that uses multi-step reasoning.
    
    The agent autonomously:
    1. Analyzes the job description to extract key requirements
    2. Analyzes the CV to identify relevant experiences
    3. Creates a strategy for tailoring
    4. Generates the HTML CV
    5. Validates the output
    6. Refines if needed
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.html_template = self._load_html_template()
        self.max_refinement_rounds = 3  # Maximum refinement rounds (reduced from 5 for faster generation)
    
    def _load_html_template(self) -> str:
        """Load the HTML template for formatting guidance"""
        template_path = os.path.join(
            os.path.dirname(__file__),
            'generate_cv_template.html'
        )
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""
    
    def _format_cv_text_from_parsed_data(self, parsed_data: Dict[str, Any]) -> str:
        """Convert parsed CV JSON data into plain text format"""
        lines = []
        
        # Personal Information
        personal_info = parsed_data.get("personal_info", {})
        if personal_info:
            name = f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}".strip()
            if name:
                lines.append(f"### {name}")
                lines.append("")
            
            contact = []
            if personal_info.get('email'):
                contact.append(f"Email: {personal_info['email']}")
            if personal_info.get('phone'):
                contact.append(f"Phone: {personal_info['phone']}")
            if personal_info.get('location'):
                contact.append(f"Location: {personal_info['location']}")
            if personal_info.get('linkedin'):
                linkedin = personal_info['linkedin']
                if not linkedin.startswith('http'):
                    linkedin = f"linkedin.com/in/{linkedin}"
                contact.append(f"LinkedIn: {linkedin}")
            
            if contact:
                lines.append("**Contact Information**")
                for c in contact:
                    lines.append(f"- {c}")
                lines.append("")
        
        # Professional Summary
        summary = parsed_data.get("summary", "") or parsed_data.get("professional_summary", "")
        if summary:
            lines.append("**Professional Summary**")
            lines.append(summary)
            lines.append("")
        
        # Education
        education = parsed_data.get("education", [])
        if education:
            lines.append("**Education**")
            for edu in education:
                degree = edu.get("degree", "")
                institution = edu.get("institution", "")
                if degree or institution:
                    lines.append(f"**{degree}**" if degree else "")
                    if institution:
                        lines.append(institution)
                    if edu.get("graduation_date"):
                        lines.append(f"- Graduated: {edu['graduation_date']}")
                    if edu.get("gpa"):
                        lines.append(f"- GPA: {edu['gpa']}")
                    lines.append("")
        
        # Work Experience
        work_experience = parsed_data.get("work_experience", [])
        if work_experience:
            lines.append("**Professional Experience**")
            for exp in work_experience:
                # Handle both "title" and "job_title" field names (parser uses "job_title")
                title = exp.get("title", "") or exp.get("job_title", "")
                company = exp.get("company", "")
                if title or company:
                    lines.append(f"**{title}**" if title else "")
                    if company:
                        lines.append(company)
                    
                    start_date = exp.get("start_date", "")
                    end_date = exp.get("end_date", "") or "Present"
                    if start_date or end_date:
                        lines.append(f"{start_date} – {end_date}")
                    lines.append("")
                    
                    # Bullet points - handle multiple field name variations
                    responsibilities = (
                        exp.get("responsibilities", []) or 
                        exp.get("description", []) or
                        exp.get("achievements", [])
                    )
                    if isinstance(responsibilities, str):
                        responsibilities = [responsibilities]
                    for resp in responsibilities:
                        if resp:
                            lines.append(f"- {resp}")
                    lines.append("")
        
        # Skills
        skills = parsed_data.get("skills", {})
        if skills:
            lines.append("**Skills**")
            if isinstance(skills, dict):
                for category, skill_list in skills.items():
                    if skill_list:
                        if isinstance(skill_list, list):
                            skill_str = ", ".join(str(s) for s in skill_list if s)
                        else:
                            skill_str = str(skill_list)
                        if skill_str:
                            lines.append(f"- **{category.capitalize()}:** {skill_str}")
            elif isinstance(skills, list):
                skill_str = ", ".join(str(s) for s in skills if s)
                if skill_str:
                    lines.append(f"- {skill_str}")
            lines.append("")
        
        # Projects
        projects = parsed_data.get("projects", [])
        if projects:
            lines.append("**Projects**")
            for proj in projects:
                name = proj.get("name", "")
                if name:
                    lines.append(f"**{name}**")
                if proj.get("description"):
                    lines.append(proj["description"])
                lines.append("")
        
        # Certifications
        certifications = parsed_data.get("certifications", [])
        if certifications:
            lines.append("**Certifications**")
            for cert in certifications:
                if isinstance(cert, dict):
                    cert_name = cert.get("name", "") or cert.get("certification", "")
                    if cert_name:
                        lines.append(f"- {cert_name}")
                else:
                    lines.append(f"- {cert}")
            lines.append("")
        
        return "\n".join(lines)
    
    async def _agent_step_analyze_job(
        self,
        job_description: str,
        job_title: str,
        company: str
    ) -> Dict[str, Any]:
        """
        Agent Step 1: Analyze the job description to extract key requirements.
        The agent identifies: required skills, preferred experience, key responsibilities, 
        qualifications, and what the employer values most.
        """
        system_prompt = """Extract key job requirements from the job description. Return JSON with:
- required_skills: Hard skills explicitly required
- preferred_skills: Preferred or mentioned skills
- key_responsibilities: Main responsibilities
- qualifications: Required/preferred qualifications
- experience_level: Estimated years needed
- industry_keywords: Industry-specific terms
- soft_skills: Leadership, communication, etc.
- technologies: Tools/platforms mentioned
- what_employer_values: What employer prioritizes

Return ONLY valid JSON."""
        
        user_prompt = f"""Job Title: {job_title}
Company: {company}

Job Description:
{job_description}

Extract key requirements and what the employer values."""
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback: try to extract structured info
                analysis = {
                    "required_skills": [],
                    "preferred_skills": [],
                    "key_responsibilities": [],
                    "qualifications": [],
                    "experience_level": None,
                    "industry_keywords": [],
                    "soft_skills": [],
                    "technologies": [],
                    "what_employer_values": []
                }
            
            return {
                "step": AgentStep.ANALYZE_JOB.value,
                "success": True,
                "analysis": analysis
            }
        except Exception as e:
            return {
                "step": AgentStep.ANALYZE_JOB.value,
                "success": False,
                "error": str(e),
                "analysis": {}
            }
    
    async def _agent_step_analyze_cv(
        self,
        cv_text: str,
        job_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent Step 2: Analyze the CV to identify relevant experiences and skills.
        The agent matches CV content to job requirements and identifies what to emphasize.
        """
        system_prompt = """Analyze CV relevance to job requirements. Return JSON with:
- relevant_experiences: Matching work experiences (with relevance score 1-10)
- relevant_skills: Skills matching job requirements
- matching_achievements: Achievements aligning with job needs
- gaps: Weak areas for this job
- strengths: Key strengths to emphasize
- recommended_emphasis: Sections/content to prioritize

Return ONLY valid JSON."""
        
        # Safely serialize job analysis
        try:
            job_summary = json.dumps(job_analysis, indent=2, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            print(f"⚠️ Error serializing job_analysis in analyze_cv step: {e}")
            # Convert to dict and handle non-serializable types
            job_analysis_clean = {}
            for key, value in job_analysis.items():
                try:
                    json.dumps(value, default=str)
                    job_analysis_clean[key] = value
                except (TypeError, ValueError):
                    job_analysis_clean[key] = str(value)
            job_summary = json.dumps(job_analysis_clean, indent=2, default=str, ensure_ascii=False)
        
        user_prompt = f"""Job Requirements:
{job_summary}

CV Content:
{cv_text}

Identify relevant experiences, skills, and what to emphasize."""
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                cv_analysis = json.loads(json_match.group())
            else:
                cv_analysis = {
                    "relevant_experiences": [],
                    "relevant_skills": [],
                    "matching_achievements": [],
                    "gaps": [],
                    "strengths": [],
                    "recommended_emphasis": []
                }
            
            return {
                "step": AgentStep.ANALYZE_CV.value,
                "success": True,
                "analysis": cv_analysis
            }
        except Exception as e:
            return {
                "step": AgentStep.ANALYZE_CV.value,
                "success": False,
                "error": str(e),
                "analysis": {}
            }
    
    async def _agent_step_analyze_job_and_cv(
        self,
        job_description: str,
        job_title: str,
        company: str,
        cv_text: str
    ) -> Dict[str, Any]:
        """
        Agent Step 1: Combined analysis of job and CV in a single call.
        Analyzes job requirements and CV relevance together for efficiency.
        """
        system_prompt = """Analyze job requirements and CV relevance together. Return JSON with two sections:

job_analysis:
- required_skills: Hard skills explicitly required
- preferred_skills: Preferred or mentioned skills
- key_responsibilities: Main responsibilities
- qualifications: Required/preferred qualifications
- experience_level: Estimated years needed
- industry_keywords: Industry-specific terms
- soft_skills: Leadership, communication, etc.
- technologies: Tools/platforms mentioned
- what_employer_values: What employer prioritizes

cv_analysis:
- relevant_experiences: Matching work experiences (with relevance score 1-10)
- relevant_skills: Skills matching job requirements
- matching_achievements: Achievements aligning with job needs
- gaps: Weak areas for this job
- strengths: Key strengths to emphasize
- recommended_emphasis: Sections/content to prioritize

Return ONLY valid JSON."""
        
        user_prompt = f"""Job Title: {job_title}
Company: {company}

Job Description:
{job_description}

CV Content:
{cv_text[:3000]}

Analyze job requirements and identify which CV experiences/skills are most relevant."""
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=3000,
                temperature=0.3
            )
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                combined_analysis = json.loads(json_match.group())
                # Extract job_analysis and cv_analysis
                job_analysis = combined_analysis.get("job_analysis", {})
                cv_analysis = combined_analysis.get("cv_analysis", {})
            else:
                # Fallback
                job_analysis = {
                    "required_skills": [],
                    "preferred_skills": [],
                    "key_responsibilities": [],
                    "qualifications": [],
                    "experience_level": None,
                    "industry_keywords": [],
                    "soft_skills": [],
                    "technologies": [],
                    "what_employer_values": []
                }
                cv_analysis = {
                    "relevant_experiences": [],
                    "relevant_skills": [],
                    "matching_achievements": [],
                    "gaps": [],
                    "strengths": [],
                    "recommended_emphasis": []
                }
            
            return {
                "step": "analyze_job_and_cv",
                "success": True,
                "job_analysis": job_analysis,
                "cv_analysis": cv_analysis
            }
        except Exception as e:
            # Fallback to separate analysis if combined fails
            print(f"⚠️ Combined analysis failed: {e}, falling back to separate steps")
            return {
                "step": "analyze_job_and_cv",
                "success": False,
                "error": str(e),
                "job_analysis": {},
                "cv_analysis": {}
            }
    
    async def _agent_step_create_strategy(
        self,
        job_analysis: Dict[str, Any],
        cv_analysis: Dict[str, Any],
        cv_text: str
    ) -> Dict[str, Any]:
        """
        Agent Step 3: Create a tailoring strategy.
        The agent decides how to structure the CV, what to emphasize, and what approach to take.
        """
        system_prompt = """Create a CV tailoring strategy. Return JSON with:
- content_priorities: What to prioritize (experience, skills, projects)
- keyword_integration: How to integrate job keywords naturally
- structure_decisions: Section order and emphasis
- tone_and_style: Tone (technical, results-focused, etc.)
- space_allocation: Space distribution across sections
- customization_approach: Specific approach (leadership, technical depth, etc.)

Return ONLY valid JSON."""
        
        # Safely serialize analysis data, handling any non-serializable objects
        try:
            job_analysis_str = json.dumps(job_analysis, indent=2, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            print(f"⚠️ Error serializing job_analysis: {e}")
            # Convert to dict and handle non-serializable types
            job_analysis_clean = {}
            for key, value in job_analysis.items():
                try:
                    json.dumps(value, default=str)
                    job_analysis_clean[key] = value
                except (TypeError, ValueError):
                    job_analysis_clean[key] = str(value)
            job_analysis_str = json.dumps(job_analysis_clean, indent=2, default=str, ensure_ascii=False)
        
        try:
            cv_analysis_str = json.dumps(cv_analysis, indent=2, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            print(f"⚠️ Error serializing cv_analysis: {e}")
            # Convert to dict and handle non-serializable types
            cv_analysis_clean = {}
            for key, value in cv_analysis.items():
                try:
                    json.dumps(value, default=str)
                    cv_analysis_clean[key] = value
                except (TypeError, ValueError):
                    cv_analysis_clean[key] = str(value)
            cv_analysis_str = json.dumps(cv_analysis_clean, indent=2, default=str, ensure_ascii=False)
        
        user_prompt = f"""Job Analysis:
{job_analysis_str}

CV Analysis:
{cv_analysis_str}

Create a strategy to maximize CV relevance and impact."""
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.4
            )
            
            # Try to extract and parse JSON with multiple strategies
            strategy = None
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                try:
                    strategy = json.loads(json_str)
                except json.JSONDecodeError as json_err:
                    # Try to fix common JSON issues
                    print(f"⚠️ JSON decode error in strategy step: {json_err}")
                    print(f"   Attempting to fix malformed JSON...")
                    
                    # Try to fix common issues
                    fixed_json = json_str
                    
                    # Fix missing quotes around keys (e.g., "ization_approach" -> "customization_approach")
                    fixed_json = re.sub(r'(\s+)([a-z_]+)(\s*):', r'\1"\2"\3:', fixed_json)
                    
                    # Fix missing quotes around string values that start without quotes
                    fixed_json = re.sub(r':\s*([A-Z][^",}\]]+?)(\s*[,}])', r': "\1"\2', fixed_json)
                    
                    # Fix truncated keys (e.g., "ization_approach" -> "customization_approach")
                    if '"ization_approach"' in fixed_json or 'ization_approach' in fixed_json:
                        fixed_json = fixed_json.replace('"ization_approach"', '"customization_approach"')
                        fixed_json = fixed_json.replace('ization_approach', 'customization_approach')
                    
                    try:
                        strategy = json.loads(fixed_json)
                        print(f"   ✅ Successfully fixed and parsed JSON")
                    except json.JSONDecodeError:
                        print(f"   ⚠️ Could not fix JSON, using fallback strategy")
                        strategy = None
            
            # Use fallback strategy if parsing failed
            if not strategy:
                strategy = {
                    "content_priorities": ["experience", "skills"],
                    "keyword_integration": "natural",
                    "structure_decisions": {},
                    "tone_and_style": "professional",
                    "space_allocation": {},
                    "customization_approach": "standard"
                }
                print(f"⚠️ Using fallback strategy for step 3 (Create Strategy)")
            
            # Validate strategy has required fields
            if not isinstance(strategy, dict):
                strategy = {
                    "content_priorities": ["experience", "skills"],
                    "keyword_integration": "natural",
                    "structure_decisions": {},
                    "tone_and_style": "professional",
                    "space_allocation": {},
                    "customization_approach": "standard"
                }
            
            return {
                "step": AgentStep.CREATE_STRATEGY.value,
                "success": True,
                "strategy": strategy
            }
        except json.JSONDecodeError as json_err:
            print(f"⚠️ JSON decode error in create_strategy: {json_err}")
            return {
                "step": AgentStep.CREATE_STRATEGY.value,
                "success": True,  # Don't fail, use fallback
                "strategy": {
                    "content_priorities": ["experience", "skills"],
                    "keyword_integration": "natural",
                    "structure_decisions": {},
                    "tone_and_style": "professional",
                    "space_allocation": {},
                    "customization_approach": "standard"
                },
                "warning": f"Used fallback strategy due to JSON parsing error: {str(json_err)}"
            }
        except Exception as e:
            print(f"⚠️ Error in create_strategy step: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the entire process - use fallback strategy
            return {
                "step": AgentStep.CREATE_STRATEGY.value,
                "success": True,  # Don't fail, use fallback
                "strategy": {
                    "content_priorities": ["experience", "skills"],
                    "keyword_integration": "natural",
                    "structure_decisions": {},
                    "tone_and_style": "professional",
                    "space_allocation": {},
                    "customization_approach": "standard"
                },
                "warning": f"Used fallback strategy due to error: {str(e)}"
            }
    
    async def _agent_step_generate_content(
        self,
        cv_text: str,
        job_description: str,
        job_title: str,
        company: str,
        job_analysis: Dict[str, Any],
        cv_analysis: Dict[str, Any],
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent Step 4: Generate the HTML CV content based on the strategy.
        """
        # Load the original prompt template
        prompt_template_path = os.path.join(
            os.path.dirname(__file__),
            'customize_cv_and_html_prompt.txt'
        )
        try:
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        except FileNotFoundError:
            base_prompt = """You are an expert resume writer and HTML/CSS developer.
INPUT: two plain-text documents exactly as provided: the candidate's original CV and a job description.
PURPOSE: produce a single self-contained HTML document (with inline CSS) that will be directly converted to PDF."""
        
        # Safely serialize analysis and strategy data
        def safe_json_dumps(obj, default=str):
            try:
                return json.dumps(obj, indent=2, default=default, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                print(f"⚠️ Error serializing object: {e}")
                # Convert to dict and handle non-serializable types
                if isinstance(obj, dict):
                    clean_obj = {}
                    for key, value in obj.items():
                        try:
                            json.dumps(value, default=str)
                            clean_obj[key] = value
                        except (TypeError, ValueError):
                            clean_obj[key] = str(value)
                    return json.dumps(clean_obj, indent=2, default=str, ensure_ascii=False)
                return json.dumps(str(obj), indent=2, ensure_ascii=False)
        
        # Enhance prompt with agent's analysis and strategy
        agent_context = f"""
AGENT ANALYSIS:
Job: {', '.join(job_analysis.get('required_skills', [])[:5])} | {len(cv_analysis.get('relevant_experiences', []))} relevant experiences | Approach: {strategy.get('customization_approach', 'standard')}

Strategy: {safe_json_dumps(strategy)}

**CRITICAL RULES**:
1. Job titles MUST be candidate's actual previous titles (NOT "{job_title}" - that's the target job)
2. Preserve all job titles and company names exactly from original CV
3. NO invented content: Only include certifications/projects/experiences from original CV
4. Follow strategy's priorities and customization approach
"""
        
        user_prompt = base_prompt.replace("{cv_text}", cv_text).replace("{jd_text}", job_description)
        user_prompt = agent_context + "\n\n" + user_prompt
        
        # Include HTML template if available
        if self.html_template:
            user_prompt = (
                user_prompt
                + "\n\nTEMPLATE_HTML_START\n"
                + self.html_template
                + "\nTEMPLATE_HTML_END\n"
                + "\nNOTE: The HTML above is the required visual template. Produce output that conforms to it."
            )
        
        system_prompt = "You are a professional resume writer and HTML/CSS developer. Follow the user prompt exactly, incorporating the agent's analysis and strategy."
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=15000,
                temperature=0.01
            )
            
            # Sanitize HTML
            html_content = self._sanitize_html(response)
            
            return {
                "step": AgentStep.GENERATE_CONTENT.value,
                "success": True,
                "html_content": html_content
            }
        except Exception as e:
            return {
                "step": AgentStep.GENERATE_CONTENT.value,
                "success": False,
                "error": str(e),
                "html_content": None
            }
    
    async def _agent_step_validate_output(
        self,
        html_content: str,
        cv_text: str,
        job_analysis: Dict[str, Any],
        previous_validation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Agent Step 5: Validate the generated CV output.
        The agent checks if the CV meets requirements, is properly formatted, and follows the strategy.
        
        Args:
            html_content: The HTML CV to validate
            cv_text: Original CV text for reference
            job_analysis: Job analysis from step 1
            previous_validation: Previous validation result (if this is a re-validation)
        """
        system_prompt = """Validate CV quality. Return JSON with:
- is_valid_html, has_required_sections, matches_job_requirements, follows_strategy, fits_one_page: Boolean
- style_acceptable: Professional styling? (alignment, spacing, typography, layout)
- no_invented_content: ONLY original CV content? (CRITICAL: check certifications, projects, experiences)
- issues: All specific issues (detailed, actionable)
- quality_score: 1-10 (8+ good, 9+ excellent)
- needs_refinement: true if score < 8 OR critical issues OR style false OR invented content
- critical_issues: Must fix (include invented content if found)
- minor_issues: Can improve (style improvements)
- quality_feedback: A comprehensive 5-8 sentence assessment that MUST include: (1) 2-3 sentences highlighting the CV's strengths and what it does well (e.g., strong job alignment, clear structure, relevant skills, professional formatting), (2) 2-3 sentences identifying the main areas that need improvement, and (3) 1-2 sentences providing specific, actionable guidance on how to enhance the CV. Be detailed, constructive, and specific.
- recommendations: List of actionable recommendations for improvement (3-5 items)

**CRITICAL**: Verify all certifications/projects/experiences exist in original CV. Flag invented content as CRITICAL.

**STYLE**: Check alignment, spacing, typography, layout, PDF readiness.

Return ONLY valid JSON."""
        
        # Extract text content from HTML for validation - use entire content
        text_content = re.sub(r'<[^>]+>', '', html_content)
        text_content_length = len(text_content)
        
        # Use full original CV text for comparison
        original_cv_text = cv_text[:6000] if len(cv_text) > 6000 else cv_text
        
        # Log warnings for very short content
        if text_content_length < 500:
            print(f"⚠️ WARNING: CV content is very short ({text_content_length} chars) - may indicate significant deletions")
        
        validation_context = ""
        if previous_validation:
            previous_issues = previous_validation.get("issues", [])
            if previous_issues:
                validation_context = f"\n\nPrevious validation found these issues (check if they're fixed):\n" + "\n".join(f"- {issue}" for issue in previous_issues[:5])
        
        user_prompt = f"""Job Requirements:
{json.dumps(job_analysis, indent=2)}

Original CV Profile (COMPLETE - for verification against current CV):
{original_cv_text}

Current CV Content (COMPLETE - this is the ACTUAL current state to validate):
{text_content}
{validation_context}

**CRITICAL**: 
1. Compare the ENTIRE current CV content against the COMPLETE original CV profile above. Verify ALL information:
   - Personal information (name, contact details)
   - Work experience (companies, titles, dates, responsibilities)
   - Education (institutions, degrees, dates)
   - Skills (all skills listed)
   - Certifications (all certifications)
   - Projects (all projects)
   - Any other sections
2. Flag ANY invented content that doesn't exist in the original CV profile.
3. Flag ANY missing critical information from the original profile (if important sections are deleted).
4. Pay close attention to the ACTUAL current CV content. If content is very short or missing sections compared to the original profile, this indicates significant deletions - flag this as a critical issue.
5. Do NOT assume content exists if it's not in the "Current CV Content" section above.

**PROFILE VERIFICATION**: 
- Cross-reference every piece of information in the current CV against the original CV profile.
- Ensure dates, company names, job titles, education details, certifications, and skills match the original profile.
- If the current CV has less content than the original profile, identify what's missing.

**STYLE**: Check professional appearance, alignment, spacing, typography, layout, PDF readiness.

**CONTENT COMPLETENESS**: 
- Compare the completeness of current CV against the original profile.
- If the CV content is very short (less than 500 characters of text) or missing major sections from the original profile, this is a CRITICAL issue.

List ALL issues (critical and minor).

Provide comprehensive quality_feedback (5-8 sentences) that MUST include:
1. 2-3 sentences on CV strengths (what it does well - job alignment, structure, skills, formatting, content quality) - ONLY mention strengths that actually exist in the current content
2. 2-3 sentences on areas needing improvement (specific weaknesses or gaps) - be specific about what's missing or inadequate
3. 1-2 sentences with actionable guidance on how to improve (concrete steps or suggestions)

Be specific, constructive, and detailed in your feedback. Base your assessment ONLY on what is actually present in the "Current CV Content" section above."""
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.2
            )
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                validation = json.loads(json_match.group())
            else:
                # Basic validation
                is_valid = self._looks_like_html(html_content)
                validation = {
                    "is_valid_html": is_valid,
                    "has_required_sections": True,
                    "matches_job_requirements": True,
                    "follows_strategy": True,
                    "fits_one_page": True,
                    "issues": [] if is_valid else ["HTML structure may be invalid"],
                    "critical_issues": [] if is_valid else ["HTML structure may be invalid"],
                    "minor_issues": [],
                    "quality_score": 7 if is_valid else 5,
                    "needs_refinement": not is_valid
                }
            
            return {
                "step": AgentStep.VALIDATE_OUTPUT.value,
                "success": True,
                "validation": validation
            }
        except Exception as e:
            # Fallback validation
            is_valid = self._looks_like_html(html_content)
            return {
                "step": AgentStep.VALIDATE_OUTPUT.value,
                "success": True,
                "validation": {
                    "is_valid_html": is_valid,
                    "has_required_sections": True,
                    "matches_job_requirements": True,
                    "follows_strategy": True,
                    "fits_one_page": True,
                    "issues": [f"Validation error: {str(e)}"] if not is_valid else [],
                    "critical_issues": [f"Validation error: {str(e)}"] if not is_valid else [],
                    "minor_issues": [],
                    "quality_score": 6 if is_valid else 4,
                    "needs_refinement": not is_valid
                }
            }
    
    async def _agent_step_refine_output(
        self,
        html_content: str,
        validation: Dict[str, Any],
        issues: List[str],
        cv_text: str,
        job_description: str,
        refinement_round: int = 1
    ) -> Dict[str, Any]:
        """
        Agent Step 6: Refine the CV output based on validation feedback.
        
        Args:
            html_content: Current HTML CV
            validation: Validation result with issues
            issues: List of issues to fix
            cv_text: Original CV text
            job_description: Job description
            refinement_round: Current refinement round number
        """
        system_prompt = """Refine CV based on validation feedback. Fix ALL issues systematically. Return complete refined HTML document."""
        
        # Separate critical and minor issues if available
        critical_issues = validation.get("critical_issues", [])
        minor_issues = validation.get("minor_issues", [])
        
        if critical_issues or minor_issues:
            issues_text = ""
            if critical_issues:
                issues_text += "CRITICAL ISSUES (must fix):\n" + "\n".join(f"- {issue}" for issue in critical_issues) + "\n\n"
            if minor_issues:
                issues_text += "MINOR ISSUES (should fix):\n" + "\n".join(f"- {issue}" for issue in minor_issues) + "\n\n"
            if issues and not (critical_issues or minor_issues):
                issues_text += "ALL ISSUES:\n" + "\n".join(f"- {issue}" for issue in issues)
        else:
            issues_text = "\n".join(f"- {issue}" for issue in issues)
        
        quality_score = validation.get("quality_score", 7)
        
        user_prompt = f"""Refine CV (Round {refinement_round}) - Quality: {quality_score}/10

Issues:
{issues_text}

Original CV: {cv_text[:500]}...
Job: {job_description[:300]}...
Current HTML: {html_content[:8000]}...

**FIX ALL ISSUES**:
1. Address all identified issues systematically
2. **STYLE**: Professional styling - alignment, spacing, typography, layout, PDF-ready CSS
3. **PRESERVE**: All factual content (job titles, companies, dates, skills)
4. **VALIDATE**: HTML validity, one-page A4 format

Return complete refined HTML with all issues resolved."""
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=15000,
                temperature=0.01
            )
            
            refined_html = self._sanitize_html(response)
            
            return {
                "step": AgentStep.REFINE_OUTPUT.value,
                "success": True,
                "html_content": refined_html
            }
        except Exception as e:
            return {
                "step": AgentStep.REFINE_OUTPUT.value,
                "success": False,
                "error": str(e),
                "html_content": html_content  # Return original if refinement fails
            }
    
    def _sanitize_html(self, html_src: str) -> str:
        """Clean and normalize HTML output"""
        if not html_src:
            return html_src
        
        # Remove code fences
        html = re.sub(r'```(?:html|\w+)?\s*', '', html_src, flags=re.IGNORECASE)
        html = html.replace('```', '')
        html = html.replace('\t', '    ')
        html = re.sub(r'(?im)^[^\S\r\n]*.*copyright.*$', '', html)
        html = re.sub(r'(?im)^.*©.*$', '', html)
        html = re.sub(r'\n{3,}', '\n\n', html)
        html = html.replace('\r\n', '\n').strip()
        
        # Extract only HTML content (from <!DOCTYPE or <html to </html>)
        # This removes any explanatory text before or after the HTML
        html_start_pattern = r'(?:<!DOCTYPE\s+html[^>]*>|<html[^>]*>)'
        html_end_pattern = r'</html>'
        
        # Find HTML start
        html_start_match = re.search(html_start_pattern, html, re.IGNORECASE)
        if html_start_match:
            html_start_pos = html_start_match.start()
            # Find HTML end
            html_end_match = re.search(html_end_pattern, html[html_start_pos:], re.IGNORECASE)
            if html_end_match:
                html_end_pos = html_start_pos + html_end_match.end()
                html = html[html_start_pos:html_end_pos]
        
        # Remove "What has been fixed" section and similar metadata
        # This section can appear inside the HTML body (before </body>) or after </html>
        
        # First, find the last proper closing tag before </body> (like </div>, </section>, etc.)
        body_end_pos = html.rfind('</body>')
        if body_end_pos != -1:
            # Find content between the last closing tag and </body>
            # Look for the last occurrence of common closing tags (including </div>)
            last_closing_tag_pattern = r'(</(?:div|section|main|article|footer|header|ul|ol|p)>)'
            matches = list(re.finditer(last_closing_tag_pattern, html[:body_end_pos], re.IGNORECASE))
            
            if matches:
                # Get position after the last closing tag
                last_tag_end = matches[-1].end()
                # Check what's between last tag and </body>
                content_before_body = html[last_tag_end:body_end_pos].strip()
                
                # If there's markdown or explanatory text, remove it
                if content_before_body:
                    # Check if it contains markdown patterns (**, |, etc.) or explanatory text
                    if (re.search(r'\*\*.*\*\*', content_before_body) or 
                        re.search(r'\|.*\|', content_before_body) or
                        re.search(r'(?i)(what has been fixed|resulting document|polished)', content_before_body)):
                        # Remove everything between last tag and </body>
                        html = html[:last_tag_end] + '\n</body>' + html[body_end_pos + 7:]
                        body_end_pos = html.rfind('</body>')  # Update position
        
        # Remove markdown-style "What has been fixed" section with table (catch any remaining)
        html = re.sub(
            r'(?i)(\*\*What has been fixed\*\*|What has been fixed)[\s\S]*?(?=</html>|</body>|$)',
            '',
            html
        )
        # Remove standalone markdown tables (Issue | Resolution format)
        html = re.sub(
            r'\|[^\n]*Issue[^\n]*\|[^\n]*Resolution[^\n]*\|[^\n]*\n\|[^\n]*[-:]+[^\n]*\|[^\n]*\n(\|[^\n]*\|[^\n]*\n)*',
            '',
            html,
            flags=re.IGNORECASE
        )
        # Remove any remaining explanatory text patterns that look like metadata
        html = re.sub(
            r'(?i)(The resulting document is|resulting document|polished.*one.*page)[\s\S]*?(?=</html>|</body>|$)',
            '',
            html
        )
        # Remove any text after </html> tag
        html_end_pos = html.rfind('</html>')
        if html_end_pos != -1:
            html = html[:html_end_pos + 7]  # Keep </html> tag
        # Ensure no content between </body> and </html>
        body_end_pos = html.rfind('</body>')
        if body_end_pos != -1 and html_end_pos != -1:
            content_between = html[body_end_pos + 7:html_end_pos].strip()
            if content_between and not content_between.startswith('</'):
                # Remove any non-HTML content between </body> and </html>
                html = html[:body_end_pos + 7] + html[html_end_pos:]
        
        html = html.strip()
        
        return html
    
    def _looks_like_html(self, text: str) -> bool:
        """Check if text looks like HTML"""
        if not text:
            return False
        text_lower = text.lstrip().lower()
        return text_lower.startswith("<!doctype") or "<html" in text_lower

    def _extract_validation_issues(self, validation: Dict[str, Any]) -> List[str]:
        """Normalize validation issues into a flat list of strings"""
        if not validation:
            return []

        issues: List[str] = []
        issues_raw = validation.get("issues", [])

        if isinstance(issues_raw, dict):
            issues.extend(issues_raw.get("critical_issues", []))
            issues.extend(issues_raw.get("minor_issues", []))
        elif isinstance(issues_raw, list):
            issues.extend(issues_raw)
        elif issues_raw:
            issues.append(str(issues_raw))

        if validation.get("critical_issues"):
            issues.extend(validation.get("critical_issues", []))
        if validation.get("minor_issues"):
            issues.extend(validation.get("minor_issues", []))

        cleaned = []
        for issue in issues:
            if issue:
                cleaned.append(str(issue).strip())
        return cleaned
    
    async def generate_tailored_cv_html(
        self,
        cv_parsed_data: Dict[str, Any],
        job_description: str,
        job_title: str = "",
        company: str = "",
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Agentic CV generation using multi-step reasoning.
        
        The agent autonomously:
        1. Analyzes the job
        2. Analyzes the CV
        3. Creates a strategy
        4. Generates content
        5. Validates output
        6. Refines if needed
        """
        # Format CV text
        cv_text = self._format_cv_text_from_parsed_data(cv_parsed_data)
        
        if not cv_text:
            return {
                "html_content": None,
                "emphasis_notes": "CV data is empty or invalid",
                "success": False,
                "error": "CV data is empty or invalid",
                "agent_steps": []
            }
        
        agent_steps = []
        html_content = None
        emphasis_notes = ""
        
        try:
            # Step 1: Combined Analysis (Job + CV) - Optimized to reduce LLM calls
            print("🤖 Agent Step 1: Analyzing job requirements and CV relevance...")
            combined_analysis_result = await self._agent_step_analyze_job_and_cv(
                job_description, job_title, company, cv_text
            )

            if combined_analysis_result["success"]:
                agent_steps.append({
                    "step": AgentStep.ANALYZE_JOB.value,
                    "success": True,
                    "analysis": combined_analysis_result.get("job_analysis", {})
                })
                agent_steps.append({
                    "step": AgentStep.ANALYZE_CV.value,
                    "success": True,
                    "analysis": combined_analysis_result.get("cv_analysis", {})
                })
                job_analysis = combined_analysis_result.get("job_analysis", {})
                cv_analysis = combined_analysis_result.get("cv_analysis", {})
            else:
                print("⚠️ Combined analysis failed, falling back to separate analysis steps...")
                job_analysis_result = await self._agent_step_analyze_job(
                    job_description, job_title, company
                )
                agent_steps.append(job_analysis_result)
                if not job_analysis_result["success"]:
                    raise Exception(f"Job analysis failed: {job_analysis_result.get('error')}")
                job_analysis = job_analysis_result["analysis"]

                cv_analysis_result = await self._agent_step_analyze_cv(cv_text, job_analysis)
                agent_steps.append(cv_analysis_result)
                if not cv_analysis_result["success"]:
                    raise Exception(f"CV analysis failed: {cv_analysis_result.get('error')}")
                cv_analysis = cv_analysis_result["analysis"]
            
            # Step 2: Create Strategy
            print("🤖 Agent Step 2: Creating tailoring strategy...")
            strategy_result = await self._agent_step_create_strategy(
                job_analysis, cv_analysis, cv_text
            )
            agent_steps.append(strategy_result)
            
            if not strategy_result["success"]:
                raise Exception(f"Strategy creation failed: {strategy_result.get('error')}")
            
            strategy = strategy_result["strategy"]
            
            # Generate emphasis notes from analysis
            relevant_skills = cv_analysis.get("relevant_skills", [])[:5]
            strengths = cv_analysis.get("strengths", [])[:3]
            emphasis_notes = f"CV tailored for {job_title} at {company}. "
            if relevant_skills:
                emphasis_notes += f"Emphasized skills: {', '.join(relevant_skills)}. "
            if strengths:
                emphasis_notes += f"Key strengths: {', '.join(strengths)}."
            
            # Step 3: Generate Content
            print("🤖 Agent Step 3: Generating CV content...")
            generation_result = await self._agent_step_generate_content(
                cv_text, job_description, job_title, company,
                job_analysis, cv_analysis, strategy
            )
            agent_steps.append(generation_result)
            
            if not generation_result["success"]:
                raise Exception(f"Content generation failed: {generation_result.get('error')}")
            
            html_content = generation_result["html_content"]
            
            if not html_content or not self._looks_like_html(html_content):
                raise Exception("Generated content is not valid HTML")
            
            # Normalize @page margins to ensure consistency (8mm 10mm)
            html_content = self._normalize_page_margins(html_content)
            
            # Step 4: Validate Output (only refine when necessary)
            print("🤖 Agent Step 4: Validating output...")
            validation_result = await self._agent_step_validate_output(
                html_content, cv_text, job_analysis
            )
            agent_steps.append(validation_result)
            validation = validation_result.get("validation", {}) or {}

            if not validation:
                raise Exception("Validation failed to return results")

            validation_issues = self._extract_validation_issues(validation)
            if validation_issues:
                validation["issues"] = validation_issues
            needs_refinement = validation.get("needs_refinement", False)
            quality_score = validation.get("quality_score", 0)

            force_style_round = not validation.get("style_acceptable", True)
            force_fact_round = not validation.get("no_invented_content", True)
            min_refinement_rounds = 1 if (force_style_round or force_fact_round) else 0
            skip_revalidation_rounds = {2} if self.max_refinement_rounds > 2 else set()
            pending_revalidation = False

            if not needs_refinement and not validation_issues and quality_score >= 8:
                print("✅ Validation passed with high quality. Skipping refinement.")
                # Ensure margins are normalized before returning
                html_content = self._normalize_page_margins(html_content)
                return {
                    "html_content": html_content,
                    "emphasis_notes": emphasis_notes,
                    "success": True,
                    "error": None,
                    "agent_steps": agent_steps,
                    "refinement_rounds": 0,
                    "final_quality_score": validation.get("quality_score", 0),
                    "agent_analysis": {
                        "job_analysis": job_analysis,
                        "cv_analysis": cv_analysis,
                        "strategy": strategy,
                        "validation": validation
                    }
                }

            # Step 5: Iterative Refinement (reduced rounds, optimized)
            refinement_round = 0
            previous_issues = set()
            
            while refinement_round < self.max_refinement_rounds:
                needs_refinement = validation.get("needs_refinement", False)
                quality_score = validation.get("quality_score", 10)
                issues = self._extract_validation_issues(validation)
                if issues:
                    validation["issues"] = issues
                
                # Always perform at least one refinement round for style validation
                if refinement_round < min_refinement_rounds:
                    print(f"🤖 Performing mandatory refinement round {refinement_round + 1} to ensure style quality...")
                    # Add style check to issues if none exist
                    if not issues:
                        issues = ["Style and formatting review needed to ensure professional appearance"]
                        validation["issues"] = issues
                        validation["needs_refinement"] = True
                
                # After minimum rounds, check stopping conditions
                elif refinement_round >= min_refinement_rounds:
                    # Stop if quality is good enough and no issues
                    if not needs_refinement and quality_score >= 8 and not issues:
                        print(f"✅ CV quality is excellent (score: {quality_score}). Refinement complete.")
                        break
                    
                    # Stop if no issues at all
                    if not issues:
                        print(f"✅ No issues found. CV is ready (quality score: {quality_score}).")
                        break
                    
                    # Note: We don't check for same issues here because we need to refine first,
                    # then re-validate to see if issues changed. This check happens after re-validation.
                
                # Refine the CV
                refinement_round += 1
                print(f"🤖 Agent Step 5 (Round {refinement_round}/{self.max_refinement_rounds}): Refining CV...")
                print(f"   Found {len(issues)} issues: {', '.join(issues[:3])}{'...' if len(issues) > 3 else ''}")
                
                # Store current issues before refinement for comparison
                current_issues_set = set(str(issue).lower() for issue in issues)
                
                refinement_result = await self._agent_step_refine_output(
                    html_content, validation, issues, cv_text, job_description, refinement_round
                )
                agent_steps.append({
                    **refinement_result,
                    "refinement_round": refinement_round
                })
                
                if not refinement_result["success"]:
                    print(f"⚠️ Refinement round {refinement_round} failed. Using previous version.")
                    break
                
                html_content = refinement_result["html_content"]
                
                # Normalize @page margins after refinement to ensure consistency
                html_content = self._normalize_page_margins(html_content)
                
                # Re-validate after refinement (skip on some rounds to save LLM calls)
                should_revalidate = (
                    refinement_round < self.max_refinement_rounds and 
                    refinement_round not in skip_revalidation_rounds
                )
                
                if should_revalidate:
                    print(f"   Re-validating after refinement round {refinement_round}...")
                    validation_result = await self._agent_step_validate_output(
                        html_content, cv_text, job_analysis, previous_validation=validation
                    )
                    agent_steps.append({
                        **validation_result,
                        "refinement_round": refinement_round,
                        "is_revalidation": True
                    })
                    validation = validation_result.get("validation", {})
                    pending_revalidation = False
                    
                    # Get new issues from re-validation
                    new_quality_score = validation.get("quality_score", quality_score)
                    new_issues = self._extract_validation_issues(validation)
                    new_issues_set = set(str(issue).lower() for issue in new_issues)
                    
                    # Check if we've improved
                    if len(new_issues) == 0:
                        print(f"   ✅ All issues resolved! Quality score: {new_quality_score}")
                        break
                    elif new_quality_score >= quality_score and len(new_issues) < len(issues):
                        print(f"   ✅ Improvement: Quality {quality_score} → {new_quality_score}, Issues {len(issues)} → {len(new_issues)}")
                        # Continue to next round - update validation state
                        quality_score = new_quality_score
                        issues = new_issues
                        previous_issues = current_issues_set
                    elif new_issues_set == current_issues_set and refinement_round >= 2:
                        # Same issues as before refinement - no progress (but allow at least 2 rounds)
                        print(f"   ⚠️ No progress: Same issues after refinement round {refinement_round}. Stopping.")
                        break
                    else:
                        # Different issues or first/second round - continue refining
                        print(f"   ⚠️ Still {len(new_issues)} issues remaining. Quality: {new_quality_score}")
                        # Update validation state for next iteration
                        quality_score = new_quality_score
                        issues = new_issues
                        previous_issues = current_issues_set
                else:
                    # Skip re-validation on this round - assume improvement and continue
                    print(f"   ⏭️ Skipping re-validation on round {refinement_round} (optimization)")
                    pending_revalidation = True
                    validation["needs_refinement"] = True
                    if not validation.get("issues"):
                        validation["issues"] = list(current_issues_set)
                    previous_issues = current_issues_set
            
            if refinement_round >= self.max_refinement_rounds:
                print(f"⚠️ Reached maximum refinement rounds ({self.max_refinement_rounds}). Using best version.")

            if pending_revalidation:
                print("🔁 Running final validation after skipped re-validation...")
                final_validation_result = await self._agent_step_validate_output(
                    html_content, cv_text, job_analysis, previous_validation=validation
                )
                agent_steps.append({
                    **final_validation_result,
                    "is_revalidation": True,
                    "final_validation": True
                })
                validation = final_validation_result.get("validation", validation)
            
            # Normalize @page margins before returning final HTML
            html_content = self._normalize_page_margins(html_content)
            
            return {
                "html_content": html_content,
                "emphasis_notes": emphasis_notes,
                "success": True,
                "error": None,
                "agent_steps": agent_steps,
                "refinement_rounds": refinement_round,
                "final_quality_score": validation.get("quality_score", 0),
                "agent_analysis": {
                    "job_analysis": job_analysis,
                    "cv_analysis": cv_analysis,
                    "strategy": strategy,
                    "validation": validation
                }
            }
            
        except Exception as e:
            return {
                "html_content": html_content,
                "emphasis_notes": emphasis_notes or f"CV tailored for {job_title} at {company}",
                "success": False,
                "error": str(e),
                "agent_steps": agent_steps
            }
    
    async def generate_tailored_cv_html_stream(
        self,
        cv_parsed_data: Dict[str, Any],
        job_description: str,
        job_title: str = "",
        company: str = "",
        max_attempts: int = 3
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming version of CV generation that yields step updates in real-time.
        Yields step updates as they happen, then yields the final result.
        """
        # Format CV text
        cv_text = self._format_cv_text_from_parsed_data(cv_parsed_data)
        
        if not cv_text:
            yield {
                "type": "error",
                "error": "CV data is empty or invalid",
                "agent_steps": []
            }
            return
        
        agent_steps = []
        html_content = None
        emphasis_notes = ""
        
        try:
            # Step 1: Combined Analysis (Job + CV)
            yield {"type": "step_start", "step": AgentStep.ANALYZE_JOB.value, "message": "Analyzing job requirements..."}
            print("🤖 Agent Step 1: Analyzing job requirements and CV relevance...")
            combined_analysis_result = await self._agent_step_analyze_job_and_cv(
                job_description, job_title, company, cv_text
            )

            if combined_analysis_result["success"]:
                step_job = {
                    "step": AgentStep.ANALYZE_JOB.value,
                    "success": True,
                    "analysis": combined_analysis_result.get("job_analysis", {})
                }
                agent_steps.append(step_job)
                yield {"type": "step_complete", "step_data": step_job}
                
                step_cv = {
                    "step": AgentStep.ANALYZE_CV.value,
                    "success": True,
                    "analysis": combined_analysis_result.get("cv_analysis", {})
                }
                agent_steps.append(step_cv)
                yield {"type": "step_complete", "step_data": step_cv}
                
                job_analysis = combined_analysis_result.get("job_analysis", {})
                cv_analysis = combined_analysis_result.get("cv_analysis", {})
            else:
                print("⚠️ Combined analysis failed, falling back to separate analysis steps...")
                yield {"type": "step_start", "step": AgentStep.ANALYZE_JOB.value, "message": "Analyzing job requirements (fallback)..."}
                job_analysis_result = await self._agent_step_analyze_job(
                    job_description, job_title, company
                )
                agent_steps.append(job_analysis_result)
                yield {"type": "step_complete", "step_data": job_analysis_result}
                if not job_analysis_result["success"]:
                    raise Exception(f"Job analysis failed: {job_analysis_result.get('error')}")
                job_analysis = job_analysis_result["analysis"]

                yield {"type": "step_start", "step": AgentStep.ANALYZE_CV.value, "message": "Analyzing your CV..."}
                cv_analysis_result = await self._agent_step_analyze_cv(cv_text, job_analysis)
                agent_steps.append(cv_analysis_result)
                yield {"type": "step_complete", "step_data": cv_analysis_result}
                if not cv_analysis_result["success"]:
                    raise Exception(f"CV analysis failed: {cv_analysis_result.get('error')}")
                cv_analysis = cv_analysis_result["analysis"]
            
            # Step 2: Create Strategy
            yield {"type": "step_start", "step": AgentStep.CREATE_STRATEGY.value, "message": "Creating tailoring strategy..."}
            print("🤖 Agent Step 2: Creating tailoring strategy...")
            strategy_result = await self._agent_step_create_strategy(
                job_analysis, cv_analysis, cv_text
            )
            agent_steps.append(strategy_result)
            yield {"type": "step_complete", "step_data": strategy_result}
            
            if not strategy_result["success"]:
                raise Exception(f"Strategy creation failed: {strategy_result.get('error')}")
            
            strategy = strategy_result["strategy"]
            
            # Generate emphasis notes from analysis
            relevant_skills = cv_analysis.get("relevant_skills", [])[:5]
            strengths = cv_analysis.get("strengths", [])[:3]
            emphasis_notes = f"CV tailored for {job_title} at {company}. "
            if relevant_skills:
                emphasis_notes += f"Emphasized skills: {', '.join(relevant_skills)}. "
            if strengths:
                emphasis_notes += f"Key strengths: {', '.join(strengths)}."
            
            # Step 3: Generate Content
            yield {"type": "step_start", "step": AgentStep.GENERATE_CONTENT.value, "message": "Generating CV content..."}
            print("🤖 Agent Step 3: Generating CV content...")
            generation_result = await self._agent_step_generate_content(
                cv_text, job_description, job_title, company,
                job_analysis, cv_analysis, strategy
            )
            agent_steps.append(generation_result)
            yield {"type": "step_complete", "step_data": generation_result}
            
            if not generation_result["success"]:
                raise Exception(f"Content generation failed: {generation_result.get('error')}")
            
            html_content = generation_result["html_content"]
            
            if not html_content or not self._looks_like_html(html_content):
                raise Exception("Generated content is not valid HTML")
            
            # Normalize @page margins to ensure consistency (8mm 10mm)
            html_content = self._normalize_page_margins(html_content)
            
            # Step 4: Validate Output
            yield {"type": "step_start", "step": AgentStep.VALIDATE_OUTPUT.value, "message": "Validating output..."}
            print("🤖 Agent Step 4: Validating output...")
            validation_result = await self._agent_step_validate_output(
                html_content, cv_text, job_analysis
            )
            agent_steps.append(validation_result)
            yield {"type": "step_complete", "step_data": validation_result}
            validation = validation_result.get("validation", {}) or {}

            if not validation:
                raise Exception("Validation failed to return results")

            validation_issues = self._extract_validation_issues(validation)
            if validation_issues:
                validation["issues"] = validation_issues
            needs_refinement = validation.get("needs_refinement", False)
            quality_score = validation.get("quality_score", 0)

            force_style_round = not validation.get("style_acceptable", True)
            force_fact_round = not validation.get("no_invented_content", True)
            min_refinement_rounds = 1 if (force_style_round or force_fact_round) else 0
            skip_revalidation_rounds = {2} if self.max_refinement_rounds > 2 else set()
            pending_revalidation = False

            if not needs_refinement and not validation_issues and quality_score >= 8:
                print("✅ Validation passed with high quality. Skipping refinement.")
                html_content = self._normalize_page_margins(html_content)
                yield {
                    "type": "complete",
                    "html_content": html_content,
                    "emphasis_notes": emphasis_notes,
                    "success": True,
                    "error": None,
                    "agent_steps": agent_steps,
                    "refinement_rounds": 0,
                    "final_quality_score": validation.get("quality_score", 0)
                }
                return

            # Step 5: Iterative Refinement (if needed)
            refinement_round = 0
            previous_issues = set()
            
            while refinement_round < self.max_refinement_rounds:
                needs_refinement = validation.get("needs_refinement", False)
                quality_score = validation.get("quality_score", 10)
                
                if not needs_refinement and quality_score >= 8:
                    break
                
                if refinement_round in skip_revalidation_rounds:
                    pending_revalidation = True
                else:
                    pending_revalidation = False
                
                refinement_round += 1
                yield {
                    "type": "step_start",
                    "step": AgentStep.REFINE_OUTPUT.value,
                    "message": f"Refining CV (round {refinement_round})...",
                    "refinement_round": refinement_round
                }
                print(f"🤖 Agent Step 5: Refining CV (round {refinement_round})...")
                
                # Extract issues from validation for refinement
                validation_issues_list = self._extract_validation_issues(validation)
                
                refinement_result = await self._agent_step_refine_output(
                    html_content=html_content,
                    validation=validation,
                    issues=validation_issues_list,
                    cv_text=cv_text,
                    job_description=job_description,
                    refinement_round=refinement_round
                )
                
                if not refinement_result.get("success", False):
                    print(f"⚠️ Refinement round {refinement_round} failed, stopping refinement")
                    break
                
                # Get refined content - the function returns 'html_content' key
                refined_html = refinement_result.get("html_content")
                
                if not refined_html:
                    print(f"⚠️ Refinement round {refinement_round} returned no HTML content")
                    break
                
                agent_steps.append({
                    "step": AgentStep.REFINE_OUTPUT.value,
                    "success": True,
                    "refinement_round": refinement_round,
                    "refined_content": refined_html
                })
                yield {"type": "step_complete", "step_data": agent_steps[-1]}
                
                html_content = refined_html
                html_content = self._normalize_page_margins(html_content)
                
                if not pending_revalidation:
                    validation_result = await self._agent_step_validate_output(
                        html_content, cv_text, job_analysis
                    )
                    agent_steps.append({
                        "step": AgentStep.VALIDATE_OUTPUT.value,
                        "success": True,
                        "is_revalidation": True,
                        "validation": validation_result.get("validation", {})
                    })
                    yield {"type": "step_complete", "step_data": agent_steps[-1]}
                    validation = validation_result.get("validation", {}) or {}
                    validation_issues = self._extract_validation_issues(validation)
                    
                    if validation_issues:
                        validation["issues"] = validation_issues
                    
                    current_issues = set(validation_issues)
                    if current_issues == previous_issues:
                        print(f"⚠️ Same issues persist after refinement round {refinement_round}, stopping")
                        break
                    previous_issues = current_issues
            
            # Final validation
            if refinement_round > 0:
                yield {"type": "step_start", "step": AgentStep.VALIDATE_OUTPUT.value, "message": "Final validation..."}
                final_validation_result = await self._agent_step_validate_output(
                    html_content, cv_text, job_analysis
                )
                agent_steps.append({
                    "step": AgentStep.VALIDATE_OUTPUT.value,
                    "success": True,
                    "is_revalidation": True,
                    "validation": final_validation_result.get("validation", {})
                })
                yield {"type": "step_complete", "step_data": agent_steps[-1]}
                validation = final_validation_result.get("validation", validation)
            
            # Normalize @page margins before returning final HTML
            html_content = self._normalize_page_margins(html_content)
            
            yield {
                "type": "complete",
                "html_content": html_content,
                "emphasis_notes": emphasis_notes,
                "success": True,
                "error": None,
                "agent_steps": agent_steps,
                "refinement_rounds": refinement_round,
                "final_quality_score": validation.get("quality_score", 0)
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "html_content": html_content,
                "emphasis_notes": emphasis_notes or f"CV tailored for {job_title} at {company}",
                "success": False,
                "error": str(e),
                "agent_steps": agent_steps
            }
    
    async def refine_existing_cv(
        self,
        html_content: str,
        cv_parsed_data: Dict[str, Any],
        job_description: str,
        job_title: str = "",
        company: str = ""
    ) -> Dict[str, Any]:
        """
        Refine an existing CV without regenerating it completely.
        Validates the current CV and refines it iteratively until no issues remain.
        
        Args:
            html_content: Current HTML CV content
            cv_parsed_data: Parsed CV data (for reference)
            job_description: Job description
            job_title: Job title
            company: Company name
            
        Returns:
            Dictionary with refined HTML content and refinement details
        """
        if not html_content or not self._looks_like_html(html_content):
            return {
                "html_content": html_content,
                "success": False,
                "error": "Invalid HTML content provided",
                "refinement_rounds": 0
            }
        
        # Format CV text for reference
        cv_text = self._format_cv_text_from_parsed_data(cv_parsed_data)
        
        # Quick job analysis for context (lightweight)
        job_analysis_result = await self._agent_step_analyze_job(
            job_description, job_title, company
        )
        
        if not job_analysis_result["success"]:
            # Fallback: use basic job analysis
            job_analysis = {
                "required_skills": [],
                "key_responsibilities": [],
                "what_employer_values": []
            }
        else:
            job_analysis = job_analysis_result["analysis"]
        
        refinement_round = 0
        previous_issues = set()
        agent_steps = []
        
        # Initial validation
        print("🔍 Validating existing CV...")
        validation_result = await self._agent_step_validate_output(
            html_content, cv_text, job_analysis
        )
        agent_steps.append(validation_result)
        validation = validation_result.get("validation", {}) or {}

        if not validation:
            return {
                "html_content": html_content,
                "success": False,
                "error": "Validation failed to return results",
                "refinement_rounds": 0
            }

        validation_issues = self._extract_validation_issues(validation)
        if validation_issues:
            validation["issues"] = validation_issues
        needs_refinement = validation.get("needs_refinement", False)
        quality_score = validation.get("quality_score", 0)

        if not needs_refinement and not validation_issues and quality_score >= 8:
            print("✅ Existing CV already meets quality targets. No refinement needed.")
            return {
                "html_content": html_content,
                "success": True,
                "error": None,
                "refinement_rounds": 0,
                "final_quality_score": quality_score,
                "agent_steps": agent_steps,
                "validation": validation
            }
        
        # Iterative refinement loop
        force_style_round = not validation.get("style_acceptable", True)
        force_fact_round = not validation.get("no_invented_content", True)
        min_refinement_rounds = 1 if (force_style_round or force_fact_round) else 0
        skip_revalidation_rounds = {2} if self.max_refinement_rounds > 2 else set()
        pending_revalidation = False
        
        while refinement_round < self.max_refinement_rounds:
            needs_refinement = validation.get("needs_refinement", False)
            quality_score = validation.get("quality_score", 10)
            issues = self._extract_validation_issues(validation)
            if issues:
                validation["issues"] = issues
            
            # Always perform at least one refinement round for style validation
            if refinement_round < min_refinement_rounds:
                print(f"🤖 Performing mandatory refinement round {refinement_round + 1} to ensure style quality...")
                # Add style check to issues if none exist
                if not issues:
                    issues = ["Style and formatting review needed to ensure professional appearance"]
                    validation["issues"] = issues
                    validation["needs_refinement"] = True
            
            # After minimum rounds, check stopping conditions
            elif refinement_round >= min_refinement_rounds:
                # Stop if quality is good enough and no issues
                if not needs_refinement and quality_score >= 8 and not issues:
                    print(f"✅ CV quality is excellent (score: {quality_score}). Refinement complete.")
                    break
                
                # Stop if no issues at all
                if not issues:
                    print(f"✅ No issues found. CV is ready (quality score: {quality_score}).")
                    break
                
                # Note: We don't check for same issues here because we need to refine first,
                # then re-validate to see if issues changed. This check happens after re-validation.
            
            # Refine the CV
            refinement_round += 1
            print(f"🔧 Refining CV (Round {refinement_round}/{self.max_refinement_rounds})...")
            print(f"   Found {len(issues)} issues: {', '.join(issues[:3])}{'...' if len(issues) > 3 else ''}")
            
            # Store current issues before refinement for comparison
            current_issues_set = set(str(issue).lower() for issue in issues)
            
            refinement_result = await self._agent_step_refine_output(
                html_content, validation, issues, cv_text, job_description, refinement_round
            )
            agent_steps.append({
                **refinement_result,
                "refinement_round": refinement_round
            })
            
            if not refinement_result["success"]:
                print(f"⚠️ Refinement round {refinement_round} failed. Using previous version.")
                break
            
            html_content = refinement_result["html_content"]
            
            # Normalize @page margins after refinement to ensure consistency
            html_content = self._normalize_page_margins(html_content)
            
            # Re-validate after refinement (skip on some rounds to save LLM calls)
            should_revalidate = (
                refinement_round < self.max_refinement_rounds and 
                refinement_round not in skip_revalidation_rounds
            )
            
            if should_revalidate:
                print(f"   Re-validating after refinement round {refinement_round}...")
                validation_result = await self._agent_step_validate_output(
                    html_content, cv_text, job_analysis, previous_validation=validation
                )
                agent_steps.append({
                    **validation_result,
                    "refinement_round": refinement_round,
                    "is_revalidation": True
                })
                validation = validation_result.get("validation", {})
                pending_revalidation = False
                
                # Get new issues from re-validation
                new_quality_score = validation.get("quality_score", quality_score)
                new_issues = self._extract_validation_issues(validation)
                new_issues_set = set(str(issue).lower() for issue in new_issues)
                
                # Check if we've improved
                if len(new_issues) == 0:
                    print(f"   ✅ All issues resolved! Quality score: {new_quality_score}")
                    break
                elif new_quality_score >= quality_score and len(new_issues) < len(issues):
                    print(f"   ✅ Improvement: Quality {quality_score} → {new_quality_score}, Issues {len(issues)} → {len(new_issues)}")
                    # Continue to next round - update validation state
                    quality_score = new_quality_score
                    issues = new_issues
                    previous_issues = current_issues_set
                elif new_issues_set == current_issues_set and refinement_round >= 2:
                    # Same issues as before refinement - no progress (but allow at least 2 rounds)
                    print(f"   ⚠️ No progress: Same issues after refinement round {refinement_round}. Stopping.")
                    break
                else:
                    # Different issues or first/second round - continue refining
                    print(f"   ⚠️ Still {len(new_issues)} issues remaining. Quality: {new_quality_score}")
                    # Update validation state for next iteration
                    quality_score = new_quality_score
                    issues = new_issues
                    previous_issues = current_issues_set
            else:
                # Skip re-validation on this round - assume improvement and continue
                print(f"   ⏭️ Skipping re-validation on round {refinement_round} (optimization)")
                pending_revalidation = True
                validation["needs_refinement"] = True
                if not validation.get("issues"):
                    validation["issues"] = list(current_issues_set)
                previous_issues = current_issues_set
        
        if refinement_round >= self.max_refinement_rounds:
            print(f"⚠️ Reached maximum refinement rounds ({self.max_refinement_rounds}). Using best version.")

        if pending_revalidation:
            print("🔁 Running final validation after skipped re-validation...")
            final_validation_result = await self._agent_step_validate_output(
                html_content, cv_text, job_analysis, previous_validation=validation
            )
            agent_steps.append({
                **final_validation_result,
                "is_revalidation": True,
                "final_validation": True
            })
            validation = final_validation_result.get("validation", validation)
        
        # Normalize @page margins before returning refined HTML
        html_content = self._normalize_page_margins(html_content)
        
        return {
            "html_content": html_content,
            "success": True,
            "error": None,
            "refinement_rounds": refinement_round,
            "final_quality_score": validation.get("quality_score", 0),
            "agent_steps": agent_steps,
            "validation": validation
        }
    
    def _normalize_page_margins(self, html_content: str) -> str:
        """
        Normalize @page rule to ensure consistent margins (8mm 10mm as per prompt).
        This ensures all generated CVs use the same page margins regardless of what the LLM generates.
        """
        import re
        
        if not html_content:
            return html_content
        
        standard_page_rule = '@page { size: A4; margin: 8mm 10mm; }'
        
        # Replace any existing @page rule with the standard one
        page_pattern = r'@page\s*\{[^}]*\}'
        if re.search(page_pattern, html_content, re.IGNORECASE | re.DOTALL):
            # Replace existing @page rule
            html_content = re.sub(page_pattern, standard_page_rule, html_content, flags=re.IGNORECASE | re.DOTALL)
        else:
            # Add @page rule if it doesn't exist
            style_match = re.search(r'<style[^>]*>', html_content, re.IGNORECASE)
            if style_match:
                insert_pos = style_match.end()
                page_rule = f'\n    {standard_page_rule}\n'
                html_content = html_content[:insert_pos] + page_rule + html_content[insert_pos:]
        
        return html_content
    
    def _post_process_html_for_pdf(self, html_content: str) -> str:
        """
        Post-process HTML content to make it compatible with PDF generation libraries.
        Removes unsupported CSS features and fixes common issues.
        """
        import re
        
        if not html_content:
            return html_content
        
        # Remove @media queries (xhtml2pdf doesn't support them well)
        # xhtml2pdf has limited CSS support and @media queries cause parsing errors
        def remove_at_rules_with_braces(text, rule_name):
            """Remove CSS @rules (like @media, @keyframes) with properly balanced braces"""
            result = []
            i = 0
            text_lower = text.lower()
            rule_len = len(rule_name)
            
            while i < len(text):
                # Check if we found the @rule
                if text_lower[i:i+rule_len] == rule_name.lower():
                    # Find the opening brace
                    brace_start = text.find('{', i)
                    if brace_start == -1:
                        # No opening brace, skip this character
                        result.append(text[i])
                        i += 1
                        continue
                    
                    # Count braces to find matching closing brace
                    brace_count = 1
                    j = brace_start + 1
                    while j < len(text) and brace_count > 0:
                        if text[j] == '{':
                            brace_count += 1
                        elif text[j] == '}':
                            brace_count -= 1
                        j += 1
                    
                    # Skip the entire @rule block (from @media to closing })
                    i = j
                else:
                    result.append(text[i])
                    i += 1
            return ''.join(result)
        
        # Remove @media queries (can have nested braces)
        html_content = remove_at_rules_with_braces(html_content, '@media')
        
        # Remove @keyframes (not supported by xhtml2pdf)
        html_content = remove_at_rules_with_braces(html_content, '@keyframes')
        
        # Remove @supports queries
        html_content = remove_at_rules_with_braces(html_content, '@supports')
        
        # Also remove any remaining @media patterns that might have been missed
        # This handles edge cases where @media might be split across lines oddly
        # Add safety counter to prevent infinite loops
        max_iterations = 10
        iteration = 0
        while '@media' in html_content.lower() and iteration < max_iterations:
            prev_content = html_content
            html_content = remove_at_rules_with_braces(html_content, '@media')
            # If no change, break to avoid infinite loop
            if prev_content == html_content:
                break
            iteration += 1
        
        # Ensure proper DOCTYPE if missing
        if not html_content.strip().startswith('<!DOCTYPE'):
            html_content = '<!DOCTYPE html>\n' + html_content
        
        # Ensure html tag has lang attribute
        if '<html' in html_content and 'lang=' not in html_content[:200]:
            html_content = re.sub(r'<html\s*>', '<html lang="en">', html_content, flags=re.IGNORECASE)
        
        # Ensure charset meta tag exists
        if 'charset' not in html_content[:500].lower():
            html_content = html_content.replace(
                '<head>',
                '<head>\n  <meta charset="UTF-8">',
                1
            )
        
        # Normalize @page margins to ensure consistency
        html_content = self._normalize_page_margins(html_content)
        
        # Ensure proper box-sizing
        if 'box-sizing' not in html_content:
            style_match = re.search(r'<style[^>]*>', html_content, re.IGNORECASE)
            if style_match:
                insert_pos = style_match.end()
                box_sizing = '\n    * { box-sizing: border-box; }\n'
                html_content = html_content[:insert_pos] + box_sizing + html_content[insert_pos:]
        
        # Ensure container has proper width constraints
        if '.container' in html_content:
            html_content = re.sub(
                r'\.container\s*\{[^}]*\}',
                lambda m: m.group(0) if 'width:' in m.group(0) and 'box-sizing' in m.group(0) else 
                         (m.group(0).replace('}', ' width: 100%; box-sizing: border-box; }') if 'width:' not in m.group(0) else
                          m.group(0).replace('}', ' box-sizing: border-box; }')),
                html_content,
                flags=re.IGNORECASE | re.DOTALL
            )
        
        # Fix potential alignment issues with item-header
        # Ensure dates are properly aligned with flexbox
        if '.item-header' in html_content:
            # Ensure item-header has proper flexbox styling
            html_content = re.sub(
                r'\.item-header\s*\{[^}]*display[^}]*\}',
                lambda m: m.group(0) if 'justify-content' in m.group(0) else m.group(0).replace('{', '{ display: flex; justify-content: space-between; align-items: baseline; width: 100%; '),
                html_content,
                flags=re.IGNORECASE | re.DOTALL
            )
            # Ensure date has proper alignment
            html_content = re.sub(
                r'\.item-header\s+\.date\s*\{[^}]*\}',
                lambda m: m.group(0) if 'text-align' in m.group(0) or 'flex-shrink' in m.group(0) else m.group(0).replace('}', ' flex-shrink: 0; text-align: right; }'),
                html_content,
                flags=re.IGNORECASE | re.DOTALL
            )
        
        # Ensure print color adjustment
        if 'print-color-adjust' not in html_content and 'color-adjust' not in html_content:
            style_match = re.search(r'</style>', html_content, re.IGNORECASE)
            if style_match:
                insert_pos = style_match.start()
                color_adjust = '\n    * { print-color-adjust: exact; -webkit-print-color-adjust: exact; }\n'
                html_content = html_content[:insert_pos] + color_adjust + html_content[insert_pos:]
        
        return html_content
    
    async def generate_tailored_cv_pdf(
        self,
        html_content: str,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Convert HTML CV to PDF using multiple methods in order of quality:
        1. Playwright (best CSS support, uses Chromium browser engine)
        2. Selenium (alternative browser automation, uses Chrome)
        3. xhtml2pdf (fallback, pure Python)
        
        Args:
            html_content: HTML content to convert
            output_path: Optional path to save PDF. If provided, saves to file and returns bytes.
            
        Returns:
            PDF bytes, or None if conversion failed
            
        Raises:
            ValueError: If PDF generation fails
        """
        # Use the dedicated CV HTML to PDF service
        # save_debug_files=None will use the keep_cv_files setting from config
        pdf_service = get_cv_html2pdf_service()
        return await pdf_service.convert_to_pdf(html_content, output_path, save_debug_files=None)


# Singleton instance
_agentic_cv_service = None

def get_agentic_cv_service() -> AgenticCVService:
    """Get singleton instance of AgenticCVService"""
    global _agentic_cv_service
    if _agentic_cv_service is None:
        _agentic_cv_service = AgenticCVService()
    return _agentic_cv_service
