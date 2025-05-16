"""Repls package for handling different REPL types."""

from typing import Protocol

class ReplHandler(Protocol):
    """Protocol defining the interface for REPL handlers."""
    
    @staticmethod
    def is_supported(pane_content: str) -> bool:
        """Check if this handler supports the given pane."""
        ...
        
    @staticmethod
    def preprocess_code(text: str) -> str:
        """Preprocess code before sending to REPL."""
        ...
        
    @staticmethod
    def send_to_repl(text: str, **kwargs) -> None:
        """Send text to the REPL."""
        ...