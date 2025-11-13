"""Job matching service for CV-to-job similarity scoring"""
from typing import Dict, Any, List


class ScoreMatchService:
    """Service for scoring job matches based on CV similarity"""
    
    def __init__(self):
        pass
    
    def calculate_match_scores(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate match scores between CV and job.
        
        Note: Currently using vector similarity via JobsEngine.
        This service can be extended for additional scoring logic.
        """
        return {
            "overall_score": 0.0,
            "skill_score": 0.0,
            "experience_score": 0.0,
            "location_score": 0.0,
            "keyword_score": 0.0
        }

