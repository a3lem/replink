"""Python REPL handler module.

This module provides basic utilities for detecting and working with Python REPLs.
It handles the differences between Python versions and implementations:

- Python >= 3.13: Supports bracketed paste mode natively
- Python < 3.13: Requires line-by-line sending to preserve indentation
- IPython (any version): Supports bracketed paste mode
"""

import re


def is_ipython_repl(pane_content: str) -> bool:
    """Check if the pane content indicates an IPython REPL.
    
    This is a more specific check than is_python_repl.
    IPython supports bracketed paste mode, which allows sending multiline
    code directly without needing %cpaste or other special handling.
    
    Args:
        pane_content: The content of the pane to check.
        
    Returns:
        True if the content appears to be from an IPython REPL.
    """
    pane_content = pane_content.lower()
    
    # Check for IPython prompt patterns
    return any(
        pattern in pane_content
        for pattern in ["in [", "ipython", "ipy"]
    )


def is_python_repl(command: str) -> bool:
    """Check if the command indicates a Python REPL.
    
    Args:
        command: The command running in the pane.
        
    Returns:
        True if the command appears to be a Python REPL.
    """
    command = command.strip().lower()
    return any(cmd in command for cmd in ["python", "ipython", "jupyter", "ipy", "bpython", "ptpython"])


def preprocess_code(text: str) -> str:
    """Preprocess Python code for sending to REPL.
    
    This function:
    1. Removes excessive blank lines
    2. Detects and removes common indentation to normalize the code
    3. Ensures the text ends with a single newline
    
    Args:
        text: The Python code to preprocess.
        
    Returns:
        Preprocessed code ready for pasting.
    """
    # Remove extra blank lines (more than one consecutive)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Find common indentation to dedent the block
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    
    if non_empty_lines:
        # Find common leading whitespace
        def get_leading_whitespace(line):
            return len(line) - len(line.lstrip())
        
        # Get indentation levels for non-empty lines
        indents = [get_leading_whitespace(line) for line in non_empty_lines if line.strip()]
        
        if indents:
            # Find the minimum indent level
            common_indent = min(indents)
            
            # Dedent all lines by the common indentation
            if common_indent > 0:
                lines = [line[common_indent:] if line.strip() else line for line in lines]
                text = '\n'.join(lines)
    
    # Ensure the text ends with a single newline
    text = text.rstrip() + '\n'
    
    return text




