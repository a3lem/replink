"""Python language implementation.

This module handles Python-specific text escaping for different REPL types:
- Standard Python < 3.13: No bracketed paste support
- Standard Python >= 3.13: Has bracketed paste support
- IPython: Uses bracketed paste or %cpaste
- ptpython: Uses bracketed paste
"""

import re
import textwrap
from dataclasses import dataclass

from replink.languages.common import Piece
from replink.logging import logger


IPYTHON_PAUSE: int = 100


@dataclass
class PythonProcessor:
    """Python language implementation."""

    use_bracketed_paste: bool = True
    use_cpaste: bool = False

    def escape_text(self, text: str) -> list[Piece]:
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
        if self.use_cpaste and len(text.splitlines()) > 1:
            return [
                Piece.text("%cpaste -q\n"),
                Piece.delay(IPYTHON_PAUSE),  # Delay in milliseconds
                Piece.text(text),
                Piece.text("--\n"),
            ]

        # Apply Python preprocessing based on bracketed paste mode
        return prepare_python_blocks(text, self.use_bracketed_paste)


def prepare_python_blocks(text: str, use_bracketed_paste: bool = True) -> list[Piece]:
    """Prepare Python code for sending to REPL.

    For non-bracketed paste (Python < 3.13):
    1. Remove all blank lines (Python REPL treats them as "end of block")
    2. Dedent the code
    3. Add blank lines between indented and unindented sections
    4. Ensure proper number of trailing newlines based on code structure

    For bracketed paste (Python >= 3.13):
    1. Keep blank lines (REPL can handle them with bracketed paste)
    2. Ensure code always ends with exactly one newline

    Args:
        text: The Python code to process.
        use_bracketed_paste: Whether bracketed paste is enabled.

    Returns:
        List of text pieces to send.
    """

    logger.debug(f"raw text: {repr(text)}")

    text = text.strip("\r\n")
    # Dedent the code
    dedented_text = textwrap.dedent(text)

    # Non-bracketed paste mode - apply full preprocessing
    # Step 1: Remove ALL empty lines
    # This is critical because Python REPL interprets blank lines as "end of block"
    lines = dedented_text.split("\n")
    no_empty_lines_text = "\n".join(line for line in lines if line.strip())

    has_medial_newlines = len(no_empty_lines_text) < len(dedented_text)

    # dedented_lines = no_empty_lines

    # Step 3: Add newlines between indented and unindented lines
    # This helps REPL understand where blocks end
    # Pattern: indented line followed by unindented line (excluding elif/else/except/finally)
    # add_eol_pat = r"(\n[ \t][^\n]+\n)(?=(?:(?!elif|else|except|finally)\S|$))"
    # result = re.sub(add_eol_pat, r"\1\n", dedented_lines)

    # Step 4: Determine how many trailing newlines we need
    # Check if the last non-empty line is indented or if we have block-starting keywords
    result_lines = no_empty_lines_text.split("\n")

    # Remove trailing empty lines for analysis
    # while result_lines and not result_lines[-1].strip():
    #     result_lines.pop()

    needs_double_newline = False
    if result_lines:
        last_line = result_lines[-1]
        # Check if last line is indented
        if last_line and last_line[0] in " \t":
            needs_double_newline = True
        else:
            # Check if we have a single-line block definition
            # e.g. `def hello(): print("hello world!")`
            first_line = next(
                (line.strip() for line in result_lines if line.strip()), ""
            )
            if re.match(
                r"^(def|class|if|elif|else|for|while|with|try|except|finally|match|case)\b[^:\n]*:[^\n]+$",
                first_line,
            ):
                logger.debug("py double newline re patt matched.")
                needs_double_newline = True

    if use_bracketed_paste:
        result = dedented_text
    else:
        result = no_empty_lines_text
        result += "\n"

    logger.debug(f"{needs_double_newline=}")

    if needs_double_newline or has_medial_newlines:
        result += "\n"

    return [Piece.text(result)]
