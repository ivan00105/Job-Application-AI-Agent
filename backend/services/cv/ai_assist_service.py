"""
AI Assist Service
Provides micro AI actions for polishing CV content (improve tone, shorten, etc.)
"""
import os
import sys
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator

import httpx

from config import get_settings

# Import LLM service
services_path = os.path.join(os.path.dirname(__file__), '..', 'jobs-finder')
sys.path.insert(0, services_path)
from llm_service import llm_service

# Import logger
try:
    from backend.services.shared.llm_logger import log_llm_call
except ImportError:
    try:
        from services.shared.llm_logger import log_llm_call
    except ImportError:
        def log_llm_call(*args, **kwargs):
            pass


class AIAssistService:
    """Service for AI-assisted micro actions on CV content"""
    INTENT_PROMPTS = {
        "improve_tone": "Make this text more professional and impactful while keeping the same meaning and facts.",
        "shorten": "Make this text more concise while preserving all key information and impact.",
        "add_metrics": "Enhance this text by highlighting where quantitative metrics could be added (don't invent metrics, just suggest where they would fit).",
        "clarify": "Make this text clearer and more specific while maintaining the same meaning.",
        "professionalize": "Make this text more professional and polished, using stronger action verbs and better structure.",
        "expand": "Expand this text with more detail while keeping it concise and impactful.",
        "keyword_optimize": "Optimize this text to naturally include relevant keywords from the job description while maintaining authenticity."
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.llm_service = llm_service

    def _resolve_instruction_text(self, intent: str) -> str:
        """Convert intent key (or custom text) into an instruction for the LLM."""
        normalized = (intent or "").strip()
        if normalized in self.INTENT_PROMPTS:
            return self.INTENT_PROMPTS[normalized]
        if normalized.lower() == "custom" or not normalized:
            return "Improve this text based on your best judgment."
        if normalized.lower() == "write":
            return "Write new content based on the user's instruction."
        return intent

    def _prepare_prompts(
        self,
        selection_html: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Build system and user prompts for the LLM call."""
        system_prompt = """You are a professional resume writer. Improve the given CV content based on the user's instruction.
Return ONLY the improved HTML/text. Do NOT add explanations, comments, or markdown. Just return the improved content."""
        instruction_text = self._resolve_instruction_text(intent)
        context_prompt = self._build_context_prompt(context)
        context_section = f"\n{context_prompt}\n" if context_prompt else "\n"
        
        # Handle "write" intent differently - no existing content to improve
        if intent.lower() == "write":
            user_instruction = context.get("instruction", "") if context else ""
            user_prompt = f"""Write new CV content based on this instruction:
{user_instruction}
{context_section}
Return the content in HTML format suitable for a professional resume."""
        else:
            user_prompt = f"""Improve this CV content:
{selection_html}

Instruction: {instruction_text}
{context_section}
Return the improved content in the same HTML format."""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }

    def _strip_code_fences(self, text: str) -> str:
        """Remove markdown fences if the model returns them."""
        if not text:
            return ""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if len(lines) > 2:
                cleaned = "\n".join(lines[1:-1]).strip()
            else:
                cleaned = cleaned.replace("```", "").strip()
        return cleaned
    
    async def improve_selection(
        self,
        selection_html: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Improve a selected portion of CV content.
        
        Args:
            selection_html: HTML content to improve
            intent: Improvement intent ("improve_tone", "shorten", "add_metrics", "clarify", "professionalize")
            context: Optional context (job description, section type, etc.)
            
        Returns:
            Dictionary with improved HTML and explanation
        """
        import time
        service_start = time.time()
        
        print(f"[AI Assist Service Perf] START: improve_selection called | Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(service_start))}")
        
        prompt_start = time.time()
        prompts = self._prepare_prompts(selection_html, intent, context)
        prompt_end = time.time()
        print(f"[AI Assist Service Perf] PROMPT: Prompts prepared | Duration: {(prompt_end - prompt_start) * 1000:.2f}ms")
        
        try:
            llm_start = time.time()
            print(f"[AI Assist Service Perf] LLM_CALL: Calling LLM service | Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(llm_start))}")
            response = await llm_service.generate_text(
                prompt=prompts["user_prompt"],
                system_prompt=prompts["system_prompt"],
                max_tokens=2000,
                temperature=0.3
            )
            llm_end = time.time()
            llm_duration = (llm_end - llm_start) * 1000
            print(f"[AI Assist Service Perf] LLM_CALL: LLM response received | Duration: {llm_duration:.2f}ms ({llm_duration/1000:.2f}s)")
            
            strip_start = time.time()
            improved_html = self._strip_code_fences(response)
            strip_end = time.time()
            print(f"[AI Assist Service Perf] STRIP: Code fences stripped | Duration: {(strip_end - strip_start) * 1000:.2f}ms")
            
            service_end = time.time()
            total_duration = (service_end - service_start) * 1000
            print(f"[AI Assist Service Perf] COMPLETE: improve_selection completed | Total: {total_duration:.2f}ms ({total_duration/1000:.2f}s)")
            
            return {
                "success": True,
                "improved_html": improved_html,
                "original_html": selection_html,
                "intent": intent
            }
        except Exception as e:
            service_end = time.time()
            total_duration = (service_end - service_start) * 1000
            print(f"[AI Assist Service Perf] ERROR: improve_selection failed | Duration: {total_duration:.2f}ms | Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "improved_html": selection_html,  # Return original on error
                "original_html": selection_html
            }

    async def stream_improvement(
        self,
        selection_html: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream improved HTML as it is generated by the LLM.
        Yields dictionaries suitable for SSE responses.
        """
        if not self.llm_service.api_key:
            raise ValueError("OpenRouter API key not configured")

        prompts = self._prepare_prompts(selection_html, intent, context)
        request_data = {
            "model": self.llm_service.model,
            "messages": [
                {"role": "system", "content": prompts["system_prompt"]},
                {"role": "user", "content": prompts["user_prompt"]}
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
            "stream": True
        }
        headers = {
            "Authorization": f"Bearer {self.llm_service.api_key}",
            "HTTP-Referer": self.llm_service.http_referer or "https://github.com/your-repo",
            "X-Title": "Job Application AI Agent"
        }

        accumulated = ""
        start_time = time.time()
        chunk_received = False
        line_count = 0

        try:
            print(f"Starting stream_improvement for intent: {intent}, selection length: {len(selection_html)}")
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream(
                    "POST",
                    f"{self.llm_service.base_url}/chat/completions",
                    headers=headers,
                    json=request_data
                ) as response:
                    print(f"OpenRouter response status: {response.status_code}")
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        line_count += 1
                        if line_count % 10 == 0:
                            print(f"Processed {line_count} lines from stream, accumulated: {len(accumulated)} chars")
                        if not line:
                            continue
                        
                        # Handle SSE format: "data: {...}" or just "{...}"
                        if line.startswith("data:"):
                            payload_str = line[len("data:"):].strip()
                        else:
                            payload_str = line.strip()
                        
                        if not payload_str:
                            continue
                        
                        if payload_str == "[DONE]":
                            break
                        
                        try:
                            payload = json.loads(payload_str)
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON: {payload_str[:100]}... Error: {e}")
                            continue

                        choices = payload.get("choices", [])
                        if not choices:
                            continue
                        
                        choice = choices[0]
                        finish_reason = choice.get("finish_reason")
                        
                        # Check if stream is done
                        if finish_reason:
                            break
                        
                        delta = choice.get("delta", {}).get("content")
                        if delta:
                            chunk_received = True
                            accumulated += delta
                            yield {
                                "delta": delta,
                                "partial": accumulated
                            }

            print(f"Stream completed. Total lines: {line_count}, chunks received: {chunk_received}, accumulated length: {len(accumulated)}")
            
            # If no chunks were received, raise an error
            if not chunk_received and not accumulated:
                raise ValueError(f"No content received from AI service. Processed {line_count} lines but no content deltas. The stream may have failed or returned empty.")

            cleaned = self._strip_code_fences(accumulated)
            if not cleaned:
                cleaned = selection_html
            yield {
                "done": True,
                "improved_html": cleaned,
                "original_html": selection_html,
                "intent": intent
            }
        finally:
            duration_ms = (time.time() - start_time) * 1000
            cleaned_response = self._strip_code_fences(accumulated) or selection_html
            log_llm_call(
                provider="openrouter",
                model=self.llm_service.model,
                prompt=prompts["user_prompt"],
                system_prompt=prompts["system_prompt"],
                response=cleaned_response,
                request_data=request_data,
                duration_ms=duration_ms,
                tokens_used=None,
                metadata={"function": "stream_improvement", "intent": intent}
            )
    
    async def suggest_improvements(
        self,
        section_html: str,
        section_type: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest improvements for a CV section.
        
        Args:
            section_html: HTML content of the section
            section_type: Type of section ("summary", "experience", "skills", etc.)
            job_description: Optional job description for context
            
        Returns:
            Dictionary with suggestions
        """
        system_prompt = """Analyze CV content and suggest specific improvements. Return JSON with:
- suggestions: List of specific improvement suggestions
- priority: "high", "medium", or "low" for each suggestion
- examples: Example of improved text for each suggestion

Return ONLY valid JSON."""
        
        context = f"Section type: {section_type}"
        if job_description:
            context += f"\nJob description excerpt: {job_description[:500]}"
        
        user_prompt = f"""Analyze this CV section and suggest improvements:

{section_html}

{context}

Provide specific, actionable suggestions."""
        
        try:
            response = await llm_service.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.4
            )
            
            # Try to parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
            else:
                suggestions = {
                    "suggestions": [],
                    "priority": [],
                    "examples": []
                }
            
            return {
                "success": True,
                "suggestions": suggestions
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestions": {"suggestions": []}
            }
    
    def _build_context_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Build context prompt from context dict"""
        if not context:
            return ""
        
        parts = []
        if context.get("job_description"):
            parts.append(f"Job description: {context['job_description'][:300]}...")
        if context.get("section_type"):
            parts.append(f"Section type: {context['section_type']}")
        if context.get("target_keywords"):
            parts.append(f"Target keywords: {', '.join(context['target_keywords'][:5])}")
        
        return "\n".join(parts) if parts else ""


# Singleton instance
_ai_assist_service = None

def get_ai_assist_service() -> AIAssistService:
    """Get singleton instance of AIAssistService"""
    global _ai_assist_service
    if _ai_assist_service is None:
        _ai_assist_service = AIAssistService()
    return _ai_assist_service

