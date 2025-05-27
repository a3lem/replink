"""Language interface for repot.

This module defines the interface for language-specific text escaping.
"""

from dataclasses import dataclass
from enum import Enum, auto
# from typing import Dict, Any, List, Protocol, runtime_checkable, Union
import typing as T

class PieceType(Enum):
    """Type of piece to send."""
    TEXT = auto()
    DELAY = auto()


@dataclass
class Piece:
    """A piece of content to send to a target."""
    type: PieceType
    content: T.Union[str, float]
    
    @staticmethod
    def text(content: str) -> 'Piece':
        """Create a text piece.
        
        Args:
            content: Text content.
            
        Returns:
            Text piece.
        """
        return Piece(PieceType.TEXT, content)
    
    @staticmethod
    def delay(milliseconds: float) -> 'Piece':
        """Create a delay piece.
        
        Args:
            milliseconds: Delay in milliseconds.
            
        Returns:
            Delay piece.
        """
        return Piece(PieceType.DELAY, milliseconds)


@T.runtime_checkable
class Language(T.Protocol):
    """Protocol for all languages."""
    
    @staticmethod
    def escape_text(text: str, config: dict[str, T.Any]) -> list[Piece]:
        """Escape text for a specific language.
        
        Args:
            text: The text to escape.
            config: Configuration for the language.
            
        Returns:
            List of pieces to send in sequence.
        """
        ...


# Language registry
LANGUAGES = {}
