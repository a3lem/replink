"""Common types and protocols for replink."""

import typing as T
from typing import Protocol, runtime_checkable


@runtime_checkable
class DataclassProtocol(Protocol):
    """Protocol for dataclass instances."""
    __dataclass_fields__: T.ClassVar[dict[str, T.Any]]