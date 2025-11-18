"""
LLM call logging utility.
Logs all LLM API calls to backend/data/logs/llm folder.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Get the base directory (backend folder)
BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / "data" / "logs" / "llm"

# Try to import config to check if logging is enabled
def _is_logging_enabled() -> bool:
    """Check if LLM logging is enabled via config"""
    try:
        from backend.config import get_settings
        settings = get_settings()
        return getattr(settings, 'enable_llm_logging', True)
    except (ImportError, AttributeError):
        try:
            from config import get_settings
            settings = get_settings()
            return getattr(settings, 'enable_llm_logging', True)
        except (ImportError, AttributeError):
            # Fallback: check environment variable directly
            env_value = os.getenv('ENABLE_LLM_LOGGING', 'true').lower()
            return env_value in ('true', '1', 'yes', 'on')


def ensure_log_dir():
    """Ensure the log directory exists"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def log_llm_call(
    provider: str,  # "openrouter", "ollama", "openai"
    model: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    response: Optional[str] = None,
    error: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    tokens_used: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log an LLM API call to a JSON file.
    
    Args:
        provider: LLM provider name (openrouter, ollama, openai)
        model: Model name used
        prompt: User prompt
        system_prompt: Optional system prompt
        response: Generated response text
        error: Error message if call failed
        request_data: Full request data (for debugging)
        response_data: Full response data (for debugging)
        duration_ms: Request duration in milliseconds
        tokens_used: Number of tokens used
        metadata: Additional metadata
    """
    # Check if logging is enabled
    if not _is_logging_enabled():
        return
    
    try:
        ensure_log_dir()
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "response": response,
            "error": error,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used,
            "metadata": metadata or {}
        }
        
        # Add full request/response if available (for debugging)
        if request_data:
            log_entry["request_data"] = request_data
        if response_data:
            log_entry["response_data"] = response_data
        
        # Create filename with timestamp
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds
        filename = f"{provider}_{timestamp_str}.json"
        filepath = LOG_DIR / filename
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        
        # Also log to standard logger
        if error:
            logger.error(f"LLM call failed [{provider}/{model}]: {error}")
        else:
            logger.debug(f"LLM call logged [{provider}/{model}]: {len(prompt)} chars -> {len(response or '')} chars")
            
    except Exception as e:
        # Don't fail the main operation if logging fails
        # But log the error with full details for debugging
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Failed to log LLM call to {LOG_DIR}: {str(e)}\n{error_details}")
        # Also print to stderr as a fallback
        import sys
        print(f"ERROR: Failed to log LLM call: {str(e)}", file=sys.stderr)
        print(f"LOG_DIR: {LOG_DIR}", file=sys.stderr)
        print(f"LOG_DIR exists: {LOG_DIR.exists()}", file=sys.stderr)

