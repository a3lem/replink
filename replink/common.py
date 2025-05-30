"""Common utilities for language and target interfaces."""

import typing as T


class SendingStep:
    """Factory functions for creating sending steps."""
    
    @staticmethod
    def command(content: str, wait_for_prompt: bool = True) -> dict[str, T.Any]:
        """Create a command sending step.
        
        Args:
            content: The command to send.
            wait_for_prompt: Whether to wait for a prompt after sending.
            
        Returns:
            A command step dictionary.
        """
        return {
            'type': 'command',
            'content': content,
            'wait_for_prompt': wait_for_prompt
        }
    
    @staticmethod
    def text(content: str, wait_for_prompt: bool = False) -> dict[str, T.Any]:
        """Create a text sending step.
        
        Args:
            content: The text to send.
            wait_for_prompt: Whether to wait for a prompt after sending.
            
        Returns:
            A text step dictionary.
        """
        return {
            'type': 'text',
            'content': content,
            'wait_for_prompt': wait_for_prompt
        }
    
    @staticmethod
    def bracketed_text(content: str) -> dict[str, T.Any]:
        """Create a bracketed paste text sending step.
        
        Args:
            content: The text to send with bracketed paste.
            
        Returns:
            A bracketed paste step dictionary.
        """
        return {
            'type': 'bracketed_paste',
            'content': content
        }
    
    @staticmethod
    def delay(seconds: float) -> dict[str, T.Any]:
        """Create a delay step.
        
        Args:
            seconds: The number of seconds to delay.
            
        Returns:
            A delay step dictionary.
        """
        return {
            'type': 'delay',
            'content': seconds
        }
    
    @staticmethod
    def keypress(key: str) -> dict[str, T.Any]:
        """Create a keypress step.
        
        Args:
            key: The key to press.
            
        Returns:
            A keypress step dictionary.
        """
        return {
            'type': 'keypress',
            'content': key
        }
