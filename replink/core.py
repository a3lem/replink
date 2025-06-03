"""Core functionality for replink.

This module implements the core text sending functionality,
orchestrating the interaction between targets and languages.
"""

import time
import typing as T

from replink.targets.common import SendOptions, Target_P
from replink.languages.common import Language_P, Piece, PieceType
from replink.logging import logger


def send(
    text: str, target: Target_P, language: Language_P, send_opts: SendOptions
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
    # Escape the text for the specific language
    pieces: list[Piece] = language.escape_text(text)
    logger.debug(f"{pieces=}")

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
            target.send(content, send_opts)
