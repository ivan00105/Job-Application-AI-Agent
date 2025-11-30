"""
Base game handler interface for extensible game types.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from models.games import Game, GameAttempt


class BaseGameHandler(ABC):
    """Base class for all game type handlers"""
    
    @abstractmethod
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Validate game content structure.
        
        Args:
            content: Game content dictionary
            
        Returns:
            True if content is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def evaluate_attempt(
        self, 
        game: Game, 
        attempt: GameAttempt
    ) -> Dict[str, Any]:
        """
        Evaluate user's answer and return result.
        
        Args:
            game: The game being played
            attempt: User's attempt/answer
            
        Returns:
            Dictionary with evaluation results
        """
        pass
    
    @abstractmethod
    def calculate_score(
        self, 
        evaluation_result: Dict[str, Any]
    ) -> int:
        """
        Calculate points earned based on evaluation.
        
        Args:
            evaluation_result: Result from evaluate_attempt
            
        Returns:
            Points earned (0-100)
        """
        pass
    
    def get_default_content_template(self) -> Dict[str, Any]:
        """
        Get default content template for this game type.
        Useful for creating new games.
        
        Returns:
            Template dictionary
        """
        return {}

