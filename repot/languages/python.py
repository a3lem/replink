"""Python language implementation.

This module handles Python-specific text escaping for different REPL types:
- Standard Python < 3.13: No bracketed paste support
- Standard Python >= 3.13: Has bracketed paste support
- IPython: Uses bracketed paste or %cpaste
- ptpython: Uses bracketed paste
"""

import re
import typing as T
import textwrap

from repot.languages.interface import LANGUAGES, Piece


class PythonLanguage:
    """Python language implementation."""

    @staticmethod
    def escape_text(text: str, config: dict[str, T.Any]) -> list[Piece]:
        """Escape Python code for sending to a REPL.

        This implementation is based on vim-slime's python ftplugin handler.

        Args:
            text: The Python code to escape.
            config: Configuration for Python.
                use_ipython: Whether to use IPython.
                use_cpaste: Whether to use %cpaste with IPython.
                ipython_pause: Milliseconds to pause after sending %cpaste.
                use_bracketed_paste: Whether to use bracketed paste.

        Returns:
            List of text pieces to send.
        """

        # Normalize newlines
        text = text.replace("\r\n", "\n")

        # Check if we're using IPython with %cpaste
        if (
            config.get("use_ipython")
            and config.get("use_cpaste")
            and len(text.splitlines()) > 1
        ):
            return [
                Piece.text("%cpaste -q\n"),
                Piece.delay(config.get("ipython_pause", 100)),  # Delay in milliseconds
                Piece.text(text),
                Piece.text("--\n"),
            ]

        # Apply Python preprocessing regardless of bracketed paste mode
        # This matches vim-slime's behavior
        return prepare_python_blocks(text)


def prepare_python_blocks(text: str) -> list[Piece]:
    """Prepare Python code for sending to REPL.

    This implements vim-slime's approach for Python < 3.13 REPLs:
    1. Remove all blank lines (Python REPL treats them as "end of block")
    2. Dedent the code
    3. Add blank lines between indented and unindented sections (except for certain keywords)
    4. Ensure proper number of trailing newlines based on code structure

    Args:
        text: The preprocessed Python code.

    Returns:
        List of text pieces to send.
    """
    # Step 1: Remove ALL empty lines
    # This is critical because Python REPL interprets blank lines as "end of block"
    lines = text.split("\n")
    no_empty_lines = "\n".join(line for line in lines if line.strip())

    # Step 2: Dedent the code
    dedented_lines = textwrap.dedent(no_empty_lines)
    
    # Step 3: Add newlines between indented and unindented lines
    # This helps REPL understand where blocks end
    # Pattern: indented line followed by unindented line (excluding elif/else/except/finally)
    add_eol_pat = r"(\n[ \t][^\n]+\n)(?=(?:(?!elif|else|except|finally)\S|$))"
    result = re.sub(add_eol_pat, r"\1\n", dedented_lines)
    
    # Step 4: Determine how many trailing newlines we need
    # Check if the last non-empty line is indented or if we have block-starting keywords
    result_lines = result.split('\n')
    
    # Remove trailing empty lines for analysis
    while result_lines and not result_lines[-1].strip():
        result_lines.pop()
    
    needs_double_newline = False
    if result_lines:
        last_line = result_lines[-1]
        # Check if last line is indented
        if last_line and last_line[0] in ' \t':
            needs_double_newline = True
        else:
            # Check if we have a single-line block definition
            first_line = next((line.strip() for line in result_lines if line.strip()), '')
            if re.match(r'^(def|class|if|elif|else|for|while|with|try|except|finally)\b.*:\s*\.\.\.\s*$', first_line):
                needs_double_newline = True
    
    # Ensure proper trailing newlines
    if not result.endswith('\n'):
        result += '\n'
    
    if needs_double_newline:
        result += '\n'
    
    # Return the prepared text
    return [Piece.text(result)]


# Register the Python language
LANGUAGES["python"] = PythonLanguage
