"""Core functionality for replink.

This module implements the core text sending functionality,
orchestrating the interaction between targets and languages.
"""

import time
import typing as T

from replink.targets.interface import Target, TargetConfig, TARGETS
from replink.languages.interface import LANGUAGES, Piece, PieceType


def escape_text(text: str, language: str, config: dict[str, T.Any]) -> list[Piece]:
    """Escape text for a specific language.
    
    Args:
        text: Text to escape.
        language: Language identifier.
        config: Language configuration.
        
    Returns:
        List of pieces to send in sequence.
    """
    print(f"{text=}")
    if language not in LANGUAGES:
        # If the language isn't registered, return the text as is
        return [Piece.text(text)]
    
    return LANGUAGES[language].escape_text(text, config)


def send(
    text: str, 
    target: str, 
    target_config: TargetConfig,
    language: str,
    language_config: dict[str, T.Any]
) -> None:
    """Send text to a target REPL.
    
    Args:
        text: The text to send.
        target: The target identifier.
        target_config: Configuration for the target.
        language: The language identifier.
        language_config: Configuration for the language.
    
    Raises:
        ValueError: If the target is not found.
    """
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target}")
    
    target_impl = T.cast(Target, TARGETS[target])

    print(f"{text=}")
    print("---")
    
    # Escape the text for the specific language
    pieces = escape_text(text, language, language_config)
    
    # Send each piece to the target
    for piece in pieces:
        if piece.type == PieceType.DELAY:
            # For delays, sleep for the specified number of milliseconds
            delay_ms = T.cast(float, piece.content)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)  # Convert ms to seconds
        else:
            # For text, send it to the target
            content = T.cast(str, piece.content)
            target_impl.send(target_config, content)
