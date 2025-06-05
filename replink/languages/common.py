"""Language interface for replink.

This module defines the interface for language-specific text escaping.
"""

from dataclasses import dataclass
from enum import Enum, auto, StrEnum
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
    def text(content: str) -> "Piece":
        """Create a text piece.

        Args:
            content: Text content.

        Returns:
            Text piece.
        """
        return Piece(PieceType.TEXT, content)

    @staticmethod
    def delay(milliseconds: float) -> "Piece":
        """Create a delay piece.

        Args:
            milliseconds: Delay in milliseconds.

        Returns:
            Delay piece.
        """
        return Piece(PieceType.DELAY, milliseconds)


@T.runtime_checkable
class Language_P(T.Protocol):
    """Protocol for all languages (must be dataclass)."""

    def escape_text(self, text: str) -> list[Piece]:
        """Escape text for a specific language.

        Args:
            text: The text to escape.

        Returns:
            List of pieces to send in sequence.
        """
        ...


class Language(StrEnum):
    PYTHON = "python"
