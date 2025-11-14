"""Shared services used across multiple domains"""
from .jobsengine_client import JobsEngineClient, get_jobsengine_client

__all__ = [
    'JobsEngineClient',
    'get_jobsengine_client'
]

