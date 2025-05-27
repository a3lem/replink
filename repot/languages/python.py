"""Python language implementation.

This module handles Python-specific text escaping for different REPL types:
- Standard Python < 3.13: No bracketed paste support
- Standard Python >= 3.13: Has bracketed paste support
- IPython: Uses bracketed paste or %cpaste
- ptpython: Uses bracketed paste
"""

import re
import typing as T

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
        # Process the text to handle indentation, etc.
        processed_text = preprocess_code(text)
        
        # Check if we're using IPython with %cpaste
        if config.get('use_ipython') and config.get('use_cpaste') and len(processed_text.splitlines()) > 1:
            return [
                Piece.text("%cpaste -q\n"), 
                Piece.delay(config.get('ipython_pause', 100)),  # Delay in milliseconds
                Piece.text(processed_text), 
                Piece.text("--\n")
            ]
        
        # For standard Python without bracketed paste (< 3.13)
        # we need to process code differently
        use_bracketed_paste = config.get('use_bracketed_paste', True)
        if not use_bracketed_paste:
            return prepare_python_blocks(processed_text)
        
        # For Python with bracketed paste or other REPLs
        return [Piece.text(processed_text)]


def preprocess_code(text: str) -> str:
    """Preprocess Python code.
    
    Args:
        text: The Python code to preprocess.
        
    Returns:
        Preprocessed code ready for pasting.
    """
    # Ensure consistent line endings
    text = text.replace('\r\n', '\n')
    
    # Don't use textwrap.dedent here - we handle dedenting in prepare_python_blocks
    # to match vim-slime's behavior exactly
    
    return text


def prepare_python_blocks(text: str) -> list[Piece]:
    """Prepare Python code for non-bracketed paste.
    
    This is a direct Python translation of vim-slime's _EscapeText_python function.
    Essential for Python < 3.13 which doesn't support bracketed paste.
    
    Args:
        text: The preprocessed Python code.
        
    Returns:
        List of text pieces to send.
    """
    # Direct translation of vim-slime's approach:
    # 1. Remove ALL empty lines completely
    # Vim: let empty_lines_pat = '\(^\|\n\)\zs\(\s*\n\+\)\+'
    # This removes all lines that contain only whitespace or are empty
    # Critical for Python REPL which treats blank lines as "end of block"
    no_empty_lines = '\n'.join(line for line in text.split('\n') if line.strip())
    
    # 2. Find common indentation from the first line
    # Vim: matchstr(no_empty_lines, '^\s*')
    first_indent_match = re.match(r'^[ \t]*', no_empty_lines)
    common_indent = first_indent_match.group(0) if first_indent_match else ""
    
    # 3. Remove common indentation from all lines
    # Vim: let dedent_pat = '\(^\|\n\)\zs'.matchstr(no_empty_lines, '^\s*')
    if common_indent:
        # Match (start or newline) + common indent
        dedent_pat = r'(^|\n)' + re.escape(common_indent)
        dedented_lines = re.sub(dedent_pat, r'\1', no_empty_lines)
    else:
        dedented_lines = no_empty_lines
    
    # 4. Add extra newline after indented lines that are followed by unindented lines
    # Vim: let except_pat = '\(elif\|else\|except\|finally\)\@!'
    #      let add_eol_pat = '\n\s[^\n]\+\n\zs\ze\('.except_pat.'\S\|$\)'
    # This adds a blank line to signal end of indented block
    add_eol_pat = r'(\n[ \t][^\n]+\n)(?=(?:(?!elif|else|except|finally)\S|$))'
    result = re.sub(add_eol_pat, r'\1\n', dedented_lines)
    
    # Claude! Double check whether this if-block appears in the vim-slime implementation.
    # Ensure ends with newline for execution
    # if not result.endswith('\n'):
    #     result += '\n'
    
    # Return the prepared text
    return [Piece.text(result)]


# Register the Python language
LANGUAGES['python'] = PythonLanguage
