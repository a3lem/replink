"""Target interface for repot.

This module defines the interface that all target implementations must follow.
A target is a destination where code will be sent (e.g., tmux pane, screen window).
"""

from typing import Protocol, runtime_checkable, TypeVar, Type
from dataclasses import dataclass


T = TypeVar('T', bound='TargetConfig')


@dataclass
class TargetConfig:
    """Base config for targets."""
    pass


@runtime_checkable
class Target(Protocol):
    """Protocol for all targets."""
    
    @staticmethod
    def config() -> Type[TargetConfig]:
        """Get the target configuration type.
        
        Returns:
            The target configuration class.
        """
        ...
    
    @staticmethod
    def send(config: TargetConfig, text: str) -> None:
        """Send text to the target.
        
        Args:
            config: Target configuration.
            text: Text to send to the target.
        """
        ...


# Target registry - map from target name to target implementation
TARGETS = {}