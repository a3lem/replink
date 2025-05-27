"""Languages package for repot.

This package contains implementations of different language support for REPLs.
Currently only Python is supported.
"""

from repot.languages.interface import Language, LANGUAGES

# Import language implementations to register them
from repot.languages import python