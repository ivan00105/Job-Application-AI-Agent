"""CV parsing service using PyMuPDF, python-docx and LLM"""
import fitz
import httpx
import json
import os
import time
from typing import Dict, Any, BinaryIO
from config import get_settings

# Import LLM logger
try:
    from backend.services.shared.llm_logger import log_llm_call
except ImportError:
    try:
        from services.shared.llm_logger import log_llm_call
    except ImportError:
        # Fallback if logger not available
        def log_llm_call(*args, **kwargs):
            pass

try:
    from docx import Document
except ImportError:
    Document = None


class CVParserService:
    """Parses CV/resume files from PDF/DOCX to structured JSON"""
    
    def __init__(self):
        self.settings = get_settings()
        self.use_openrouter = bool(self.settings.openrouter_api_key)
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load CV parser prompt template from file"""
        prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'cv_parser_prompt.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""  # Fallback to inline prompt if file not found
    
    def extract_text_from_pdf(self, pdf_file: BinaryIO) -> str:
        """Extract text from PDF using PyMuPDF"""
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        text_parts = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_parts.append(page.get_text())
        
        doc.close()
        return "\n\n".join(text_parts).strip()
    
    def extract_text_from_docx(self, docx_file: BinaryIO) -> str:
        """Extract text from DOCX using python-docx"""
        if Document is None:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")
        
        doc = Document(docx_file)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        return "\n\n".join(text_parts).strip()
    
    async def parse_cv_with_llm(self, cv_text: str) -> Dict[str, Any]:
        """Parse CV text into structured JSON using LLM (OpenRouter or Ollama)"""
        if self.prompt_template:
            prompt = self.prompt_template.replace('{cv_text}', cv_text)
        else:
            prompt = f"""Extract information from this CV/resume and return ONLY valid JSON following this exact template:

{{
  "personal_info": {{
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "linkedin": "string",
    "github": "string",
    "website": "string"
  }},
  "professional_summary": "string",
  "work_experience": [
    {{
      "job_title": "string",
      "company": "string",
      "location": "string",
      "start_date": "string (YYYY-MM or MM/YYYY)",
      "end_date": "string (YYYY-MM or MM/YYYY or 'Present')",
      "responsibilities": ["string"]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "field_of_study": "string",
      "institution": "string",
      "location": "string",
      "graduation_year": "string (YYYY)",
      "gpa": "string (optional)"
    }}
  ],
  "skills": {{
    "technical": ["string"],
    "soft": ["string"],
    "tools": ["string"]
  }},
  "certifications": [
    {{
      "name": "string",
      "issuer": "string",
      "date_obtained": "string (YYYY-MM)",
      "expiry_date": "string (optional)"
    }}
  ],
  "languages": [
    {{
      "language": "string",
      "proficiency": "Native/Fluent/Professional/Intermediate/Basic"
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "description": "string",
      "technologies": ["string"],
      "url": "string (optional)"
    }}
  ]
}}

CV Text:
{cv_text}

Return ONLY the JSON, no markdown, no explanations."""

        system_prompt = "You are a precise CV parser. Return only valid JSON."
        start_time = time.time()
        
        if self.use_openrouter:
            request_data = {
                "model": self.settings.openrouter_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.settings.openrouter_base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                            "Content-Type": "application/json"
                        },
                        json=request_data
                    )
                    response.raise_for_status()
                    result = response.json()
                    generated_text = result["choices"][0]["message"]["content"]
                    
                    duration_ms = (time.time() - start_time) * 1000
                    usage = result.get("usage", {})
                    tokens_used = usage.get("total_tokens")
                    
                    # Log the LLM call
                    log_llm_call(
                        provider="openrouter",
                        model=self.settings.openrouter_model,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        response=generated_text[:500] if len(generated_text) > 500 else generated_text,  # Truncate for logging
                        request_data=request_data,
                        response_data=result,
                        duration_ms=duration_ms,
                        tokens_used=tokens_used,
                        metadata={"function": "parse_cv_with_llm", "cv_text_length": len(cv_text)}
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_msg = str(e)
                log_llm_call(
                    provider="openrouter",
                    model=self.settings.openrouter_model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    error=error_msg,
                    request_data=request_data,
                    duration_ms=duration_ms,
                    metadata={"function": "parse_cv_with_llm", "cv_text_length": len(cv_text)}
                )
                raise
        else:
            request_data = {
                "model": self.settings.ollama_chat_model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.settings.ollama_base_url}/api/generate",
                        json=request_data
                    )
                    response.raise_for_status()
                    result = response.json()
                    generated_text = result.get("response", "")
                    
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Extract token usage if available (Ollama format)
                    tokens_used = None
                    if "eval_count" in result:
                        tokens_used = result.get("eval_count")  # Ollama uses eval_count
                    
                    # Log the LLM call
                    log_llm_call(
                        provider="ollama",
                        model=self.settings.ollama_chat_model,
                        prompt=prompt,
                        system_prompt=None,  # Ollama doesn't use system prompts in /api/generate
                        response=generated_text[:500] if len(generated_text) > 500 else generated_text,  # Truncate for logging
                        request_data=request_data,
                        response_data=result,
                        duration_ms=duration_ms,
                        tokens_used=tokens_used,
                        metadata={"function": "parse_cv_with_llm", "cv_text_length": len(cv_text)}
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_msg = str(e)
                log_llm_call(
                    provider="ollama",
                    model=self.settings.ollama_chat_model,
                    prompt=prompt,
                    system_prompt=None,
                    error=error_msg,
                    request_data=request_data,
                    duration_ms=duration_ms,
                    metadata={"function": "parse_cv_with_llm", "cv_text_length": len(cv_text)}
                )
                raise
        
        try:
            generated_text = generated_text.strip()
            if generated_text.startswith("```json"):
                generated_text = generated_text[7:-3].strip()
            elif generated_text.startswith("```"):
                generated_text = generated_text[3:-3].strip()
            return json.loads(generated_text)
        except json.JSONDecodeError:
            return {
                "personal_info": {},
                "professional_summary": "",
                "work_experience": [],
                "education": [],
                "skills": {"technical": [], "soft": [], "tools": []},
                "certifications": [],
                "languages": [],
                "projects": [],
                "raw_llm_response": generated_text
            }
    
    async def parse_cv_file(self, file: BinaryIO, file_type: str = "pdf") -> Dict[str, Any]:
        """Full parsing pipeline: PDF/DOCX to structured JSON"""
        if file_type.lower() == "pdf":
            raw_text = self.extract_text_from_pdf(file)
        elif file_type.lower() in ["docx", "doc"]:
            raw_text = self.extract_text_from_docx(file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        parsed_data = await self.parse_cv_with_llm(raw_text)
        
        return {
            "raw_text": raw_text,
            "parsed_data": parsed_data
        }


_cv_parser_service: CVParserService = None


def get_cv_parser_service() -> CVParserService:
    """Get singleton CV parser service"""
    global _cv_parser_service
    if _cv_parser_service is None:
        _cv_parser_service = CVParserService()
    return _cv_parser_service

