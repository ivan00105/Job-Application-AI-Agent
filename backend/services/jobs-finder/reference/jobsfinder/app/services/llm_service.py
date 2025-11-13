"""
LLM service for query enhancement using OpenRouter API.
Uses GPT-OSS-120B model to intelligently enhance job search queries.
"""
import httpx
from typing import Optional
from app.config import settings

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_MODEL
        self.temperature = settings.OPENROUTER_TEMPERATURE
        self.max_tokens = settings.OPENROUTER_MAX_TOKENS
    
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
7. Return ONLY the enhanced query, no explanations or additional text

Examples:
- "Python developer" → "Python developer software engineer programming Python Django Flask FastAPI backend development"
- "data analyst" → "data analyst data scientist business analyst data analytics SQL Python R Tableau Power BI"
- "project manager" → "project manager program manager PMP agile scrum project coordination team leadership"
- "machine learning" → "machine learning ML engineer data scientist AI artificial intelligence deep learning neural networks TensorFlow PyTorch"
"""
        
        user_prompt = f"""Original query: {user_query}

Please enhance this query for better job search results. Expand it with relevant terms, synonyms, and related job titles while maintaining the core intent."""
        
        if context:
            user_prompt += f"\n\nContext: {context}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER or "https://github.com/your-repo",
                        "X-Title": "Job Search API"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                enhanced_query = data["choices"][0]["message"]["content"].strip()
                
                # Fallback to original query if enhancement is empty or too short
                if not enhanced_query or len(enhanced_query) < len(user_query) * 0.5:
                    return user_query
                
                return enhanced_query
                
        except httpx.HTTPError as e:
            # If LLM call fails, return original query
            print(f"Warning: LLM query enhancement failed: {str(e)}")
            return user_query
        except Exception as e:
            print(f"Warning: Unexpected error in LLM service: {str(e)}")
            return user_query
    
    async def extract_search_intent(self, user_query: str) -> dict:
        """
        Extract search intent and key information from user query.
        
        Returns:
            Dictionary with extracted information (job_title, skills, experience_level, etc.)
        """
        if not self.api_key:
            return {"original_query": user_query}
        
        system_prompt = """You are a job search intent extraction assistant. Analyze user queries and extract structured information.

Extract:
- Primary job title or role
- Required skills and technologies
- Experience level (if mentioned)
- Industry or domain
- Any specific requirements

Return a JSON object with these fields."""
        
        user_prompt = f"Analyze this job search query and extract key information: {user_query}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER or "https://github.com/your-repo",
                        "X-Title": "Job Search API"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "response_format": {"type": "json_object"}
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                import json
                intent = json.loads(data["choices"][0]["message"]["content"])
                return intent
                
        except Exception as e:
            print(f"Warning: Intent extraction failed: {str(e)}")
            return {"original_query": user_query}

llm_service = LLMService()

