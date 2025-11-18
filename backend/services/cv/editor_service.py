"""
CV Editor Service
Handles manual editing, versioning, and draft management for tailored CVs.
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import get_settings


class CVEditorService:
    """Service for managing CV editing workflow"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_edit_version(
        self,
        original_html: str,
        edited_html: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new version of the CV with user edits.
        
        Args:
            original_html: Original agent-generated HTML
            edited_html: User-edited HTML
            user_id: User ID making the edit
            notes: Optional notes about the edit
            
        Returns:
            Version metadata dictionary
        """
        version = {
            "version_id": f"edit_{datetime.utcnow().isoformat()}",
            "original_html": original_html,
            "edited_html": edited_html,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "notes": notes,
            "status": "draft"
        }
        return version
    
    def update_tailored_content_with_edit(
        self,
        tailored_content: Dict[str, Any],
        edited_html: str,
        status: str = "draft"
    ) -> Dict[str, Any]:
        """
        Update tailored_content JSON with edited HTML and versioning info.
        
        Args:
            tailored_content: Current tailored_content dict
            edited_html: User-edited HTML
            status: Status of the CV ("draft" or "final")
            
        Returns:
            Updated tailored_content dict
        """
        # Ensure we have version history
        if "version_history" not in tailored_content:
            tailored_content["version_history"] = []
        
        # Get original HTML if available
        original_html = tailored_content.get("html_content", "")
        
        # Create new version entry
        new_version = {
            "version_id": f"edit_{datetime.utcnow().isoformat()}",
            "html_content": edited_html,
            "status": status,
            "created_at": datetime.utcnow().isoformat(),
            "is_user_edit": True
        }
        
        # Add to history (keep last 10 versions)
        tailored_content["version_history"].append(new_version)
        if len(tailored_content["version_history"]) > 10:
            tailored_content["version_history"] = tailored_content["version_history"][-10:]
        
        # Update main HTML content
        tailored_content["html_content"] = edited_html
        tailored_content["status"] = status
        tailored_content["last_edited_at"] = datetime.utcnow().isoformat()
        tailored_content["has_user_edits"] = True
        
        return tailored_content
    
    def get_edit_history(
        self,
        tailored_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get edit history from tailored_content.
        
        Args:
            tailored_content: Tailored content dict
            
        Returns:
            List of version entries
        """
        return tailored_content.get("version_history", [])
    
    def get_latest_version(
        self,
        tailored_content: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest version (either agent-generated or user-edited).
        
        Args:
            tailored_content: Tailored content dict
            
        Returns:
            Latest version dict or None
        """
        history = self.get_edit_history(tailored_content)
        if history:
            return history[-1]
        return None
    
    def compare_versions(
        self,
        version1_html: str,
        version2_html: str
    ) -> Dict[str, Any]:
        """
        Compare two HTML versions and return differences.
        
        Args:
            version1_html: First version HTML
            version2_html: Second version HTML
            
        Returns:
            Comparison metadata
        """
        # Simple comparison - could be enhanced with HTML diff
        return {
            "length_diff": len(version2_html) - len(version1_html),
            "has_changes": version1_html != version2_html,
            "similarity": self._calculate_similarity(version1_html, version2_html)
        }
    
    def _calculate_similarity(self, html1: str, html2: str) -> float:
        """Calculate simple similarity ratio between two HTML strings"""
        if not html1 or not html2:
            return 0.0
        
        # Simple character-based similarity
        if html1 == html2:
            return 1.0
        
        # Count common substrings (simplified)
        common_chars = sum(1 for a, b in zip(html1, html2) if a == b)
        max_len = max(len(html1), len(html2))
        
        return common_chars / max_len if max_len > 0 else 0.0


# Singleton instance
_cv_editor_service = None

def get_cv_editor_service() -> CVEditorService:
    """Get singleton instance of CVEditorService"""
    global _cv_editor_service
    if _cv_editor_service is None:
        _cv_editor_service = CVEditorService()
    return _cv_editor_service

