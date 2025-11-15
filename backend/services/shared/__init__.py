"""Shared services used across multiple domains"""
try:
    from .jobsengine_client import JobsEngineClient, get_jobsengine_client
    __all__ = [
        'JobsEngineClient',
        'get_jobsengine_client',
        'log_llm_call'
    ]
except ImportError:
    # jobsengine_client not available, but llm_logger is
    __all__ = ['log_llm_call']

# Always export llm_logger
from .llm_logger import log_llm_call

