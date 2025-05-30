"""Languages package for replink.

This package contains implementations of different language support for REPLs.
Currently only Python is supported.
"""

from replink.languages.interface import LanguageProcessor, LANGUAGES

# Import language implementations to register them
from replink.languages import python

__all__ = [
    'LanguageProcessor', 'LANGUAGES', 'python'
]
