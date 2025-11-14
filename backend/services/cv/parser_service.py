"""CV parsing service using PyMuPDF and LLM"""
import fitz
import httpx
import json
from typing import Dict, Any, BinaryIO
from config import get_settings


class CVParserService:
    """Parses CV/resume files from PDF to structured JSON"""
    
    def __init__(self):
        self.settings = get_settings()
        self.ollama_url = self.settings.ollama_url
        self.chat_model = self.settings.ollama_chat_model
    
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
    
    async def parse_cv_with_llm(self, cv_text: str) -> Dict[str, Any]:
        """Parse CV text into structured JSON using LLM"""
        prompt = f"""You are a CV/resume parser. Extract structured information from the following CV text and return it as valid JSON.

Extract these fields:
- personal_info: {{full_name, email, phone, location, linkedin, github}}
- summary: A brief professional summary
- education: [{{degree, institution, graduation_year, gpa}}]
- work_experience: [{{job_title, company, start_date, end_date, responsibilities: [list]}}]
- skills: {{technical: [list], soft: [list]}}
- certifications: [{{name, issuer, date}}]
- languages: [{{language, proficiency}}]

CV Text:
{cv_text}

Return ONLY valid JSON, no additional text or explanation."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.chat_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            response.raise_for_status()
            result = response.json()
            generated_text = result.get("response", "")
            
            try:
                return json.loads(generated_text)
            except json.JSONDecodeError:
                return {
                    "personal_info": {},
                    "summary": "",
                    "education": [],
                    "work_experience": [],
                    "skills": {"technical": [], "soft": []},
                    "certifications": [],
                    "languages": [],
                    "raw_llm_response": generated_text
                }
    
    async def parse_cv_file(self, pdf_file: BinaryIO) -> Dict[str, Any]:
        """Full parsing pipeline: PDF to structured JSON"""
        raw_text = self.extract_text_from_pdf(pdf_file)
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

