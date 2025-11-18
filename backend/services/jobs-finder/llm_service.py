"""
LLM service for query enhancement using OpenRouter API.
Uses LLM to intelligently enhance job search queries.
"""
import httpx
from typing import Optional
import os
import logging
import time

logger = logging.getLogger(__name__)

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

# Try to import config, fallback to os.getenv
try:
    from backend.config import get_settings
    _use_config = True
except ImportError:
    try:
        from config import get_settings
        _use_config = True
    except ImportError:
        _use_config = False


class LLMService:
    """Service for LLM-based query enhancement"""
    
    def __init__(self):
        # Get settings from config if available, otherwise from environment
        if _use_config:
            try:
                settings = get_settings()
                self.api_key = settings.openrouter_api_key or ""
                self.base_url = settings.openrouter_base_url or "https://openrouter.ai/api/v1"
                self.model = settings.openrouter_model or "openrouter/gpt-oss-120b"
                self.temperature = getattr(settings, 'openrouter_temperature', 0.7)
                self.max_tokens = getattr(settings, 'openrouter_max_tokens', 200)
                self.http_referer = getattr(settings, 'openrouter_http_referer', None)
            except Exception as e:
                logger.warning(f"Failed to load config, using environment variables: {str(e)}")
                self._load_from_env()
        else:
            self._load_from_env()
    
    def _load_from_env(self):
        """Load settings from environment variables"""
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("OPENROUTER_MODEL", "openrouter/gpt-oss-120b")
        self.temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "200"))
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", None)
    
    async def enhance_job_search_query(
        self, 
        user_query: str,
        context: Optional[str] = None
    ) -> str:
        """
        Enhance a job search query using LLM to make it more effective for vector search.
        
        Args:
            user_query: The original user search query
            context: Optional context about the job search domain
            
        Returns:
            Enhanced query string optimized for semantic search
        """
        if not self.api_key:
            # If no API key, return original query
            return user_query
        
        system_prompt = """You are a job search query enhancement assistant. Your task is to transform user queries into optimized search queries for a job database.

Guidelines:
1. Expand the query with relevant synonyms, related terms, and job titles
2. Include common variations of job titles and skills
3. Add relevant technical terms, tools, and methodologies
4. Keep the enhanced query focused and relevant to the original intent
5. Don't add unrelated terms - stay true to the user's search intent
6. Make it suitable for semantic/vector search (natural language, not keywords)
7. When candidate profile context is provided, integrate their qualifications, seniority, industries, locations, unique skills, and explicit years of experience or tenure information that appear in the context. Do not invent details that are not in the context.
8. Return ONLY the enhanced query, no explanations or additional text

Examples:
- "Python developer" → "Python developer software engineer programming Python Django Flask FastAPI backend development"
- "data analyst" → "data analyst data scientist business analyst data analytics SQL Python R Tableau Power BI"
- "project manager" → "project manager program manager PMP agile scrum project coordination team leadership"
- "machine learning" → "machine learning ML engineer data scientist AI artificial intelligence deep learning neural networks TensorFlow PyTorch"
"""
        
        user_prompt = f"""Original query: {user_query}

Please enhance this query for better job search results. Expand it with relevant terms, synonyms, and related job titles while maintaining the core intent."""

        if context:
            user_prompt += (
                "\n\nCandidate profile context:\n"
                f"{context}\n"
                "Incorporate the candidate's documented qualifications, years of experience, career level, and skills "
                "above so the enhanced query reflects their background while still targeting the original intent."
            )
        
        request_data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": self.http_referer or "https://github.com/your-repo",
                        "X-Title": "Job Search API"
                    },
                    json=request_data
                )
                response.raise_for_status()
                data = response.json()
                
                duration_ms = (time.time() - start_time) * 1000
                enhanced_query = data["choices"][0]["message"]["content"].strip()
                
                # Extract token usage if available
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")
                
                # Log the LLM call
                log_llm_call(
                    provider="openrouter",
                    model=self.model,
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    response=enhanced_query,
                    request_data=request_data,
                    response_data=data,
                    duration_ms=duration_ms,
                    tokens_used=tokens_used,
                    metadata={"function": "enhance_job_search_query", "original_query": user_query, "context": context}
                )
                
                # Fallback to original query if enhancement is empty or too short
                if not enhanced_query or len(enhanced_query) < len(user_query) * 0.5:
                    return user_query
                
                return enhanced_query
                
        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            # If LLM call fails, return original query
            logger.warning(f"LLM query enhancement failed: {error_msg}")
            
            # Log the error
            log_llm_call(
                provider="openrouter",
                model=self.model,
                prompt=user_prompt,
                system_prompt=system_prompt,
                error=error_msg,
                request_data=request_data,
                duration_ms=duration_ms,
                metadata={"function": "enhance_job_search_query", "original_query": user_query, "context": context}
            )
            return user_query
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.warning(f"Unexpected error in LLM service: {error_msg}")
            
            # Log the error
            log_llm_call(
                provider="openrouter",
                model=self.model,
                prompt=user_prompt,
                system_prompt=system_prompt,
                error=error_msg,
                request_data=request_data,
                duration_ms=duration_ms,
                metadata={"function": "enhance_job_search_query", "original_query": user_query, "context": context}
            )
            return user_query
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text using LLM with a custom prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Optional max tokens (overrides default)
            temperature: Optional temperature (overrides default)
            
        Returns:
            Generated text response
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        request_data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or (self.max_tokens * 10)  # Default to 10x for longer responses
        }
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": self.http_referer or "https://github.com/your-repo",
                        "X-Title": "Job Application AI Agent"
                    },
                    json=request_data
                )
                response.raise_for_status()
                data = response.json()
                
                duration_ms = (time.time() - start_time) * 1000
                generated_text = data["choices"][0]["message"]["content"].strip()
                
                # Extract token usage if available
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")
                
                # Log the LLM call
                log_llm_call(
                    provider="openrouter",
                    model=self.model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    response=generated_text,
                    request_data=request_data,
                    response_data=data,
                    duration_ms=duration_ms,
                    tokens_used=tokens_used,
                    metadata={"function": "generate_text", "max_tokens": max_tokens, "temperature": temperature}
                )
                
                return generated_text
                
        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"LLM text generation failed: {error_msg}")
            
            # Log the error
            log_llm_call(
                provider="openrouter",
                model=self.model,
                prompt=prompt,
                system_prompt=system_prompt,
                error=error_msg,
                request_data=request_data,
                duration_ms=duration_ms,
                metadata={"function": "generate_text", "max_tokens": max_tokens, "temperature": temperature}
            )
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"Unexpected error in LLM text generation: {error_msg}")
            
            # Log the error
            log_llm_call(
                provider="openrouter",
                model=self.model,
                prompt=prompt,
                system_prompt=system_prompt,
                error=error_msg,
                request_data=request_data,
                duration_ms=duration_ms,
                metadata={"function": "generate_text", "max_tokens": max_tokens, "temperature": temperature}
            )
            raise


# Singleton instance
llm_service = LLMService()

