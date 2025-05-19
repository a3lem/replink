"""Common utilities for language and target interfaces."""

from typing import Dict, Any


class SendingStep:
    """Factory functions for creating sending steps."""
    
    @staticmethod
    def command(content: str, wait_for_prompt: bool = True) -> Dict[str, Any]:
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
    def text(content: str, wait_for_prompt: bool = False) -> Dict[str, Any]:
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
    def bracketed_text(content: str) -> Dict[str, Any]:
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
    def delay(seconds: float) -> Dict[str, Any]:
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
    def keypress(key: str) -> Dict[str, Any]:
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