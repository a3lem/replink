"""Python REPL handler module.

This module provides utilities for processing and sending Python code to different REPL types:

- Standard Python < 3.13: No bracketed paste support, needs special handling
- Standard Python >= 3.13: Has bracketed paste support
- IPython: Uses bracketed paste or %cpaste
- ptpython: Uses bracketed paste
"""

import re
import textwrap
from typing import List, Dict, Any

from repot.common import SendingStep


def preprocess_code(text: str) -> str:
    """Preprocess Python code for sending to any REPL.
    
    This performs basic preprocessing that's appropriate for all REPL types.
    
    Args:
        text: The Python code to preprocess.
        
    Returns:
        Preprocessed code ready for pasting.
    """
    # Remove extra blank lines (more than one consecutive)
    text = re.sub(r'(^|\n)\s*\n+', '\n', text)
    
    # Use textwrap.dedent to properly handle Python's indentation
    text = textwrap.dedent(text)
    
    # Ensure the text ends with a single newline
    text = text.rstrip() + '\n'
    
    return text


def format_for_sending(text: str, line_mode: bool = False, 
                      special_mode: bool = False) -> List[Dict[str, Any]]:
    """Format Python code for sending to a REPL.
    
    Args:
        text: The preprocessed Python code to format.
        line_mode: Whether to use line-by-line mode (for Python < 3.13).
        special_mode: Whether to use %cpaste (for IPython).
        
    Returns:
        A list of steps to send the code.
    """
    if special_mode:  # IPython %cpaste mode
        return _format_for_cpaste(text)
    elif line_mode:  # Python < 3.13 without bracketed paste
        return _preprocess_for_line_mode(text)
    else:  # Standard bracketed paste mode
        return [SendingStep.bracketed_text(text)]


def _format_for_cpaste(text: str) -> List[Dict[str, Any]]:
    """Format text for sending to IPython with %cpaste command.
    
    This enables reliable pasting of multi-line code in IPython.
    
    Args:
        text: The Python code to send.
        
    Returns:
        A list of steps to execute the code using %cpaste.
    """
    return [
        SendingStep.command('%cpaste -q', wait_for_prompt=False),
        SendingStep.delay(0.1),
        SendingStep.text(text, wait_for_prompt=False),
        SendingStep.command('--', wait_for_prompt=True)
    ]


def _preprocess_for_line_mode(text: str) -> List[Dict[str, Any]]:
    """Preprocess Python code for line-by-line sending to Python < 3.13.
    
    This function transforms multi-line code into a series of lines that can be 
    sent one-by-one to a Python REPL that doesn't support bracketed paste.
    It handles significant whitespace and ensures proper execution of blocks.
    
    Args:
        text: The Python code to preprocess.
        
    Returns:
        A list of steps to send the code.
    """
    lines = text.splitlines()
    result = []
    
    # Identify imports first - they need to be sent before other code
    imports = []
    non_imports = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('import ', 'from ')):
            imports.append(line)
        else:
            non_imports.append(line)
    
    # Process imports first
    for imp in imports:
        if imp.strip():  # Skip empty lines
            result.append(SendingStep.command(imp))
    
    # Track multi-line statements
    i = 0
    while i < len(non_imports):
        line = non_imports[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
            
        # Handle multi-line statements with brackets
        if ('(' in stripped or '[' in stripped or '{' in stripped) and not (stripped.endswith(')') or 
                                                                     stripped.endswith(']') or 
                                                                     stripped.endswith('}')):
            # This is the start of a multi-line collection
            # We need to identify all lines that belong to this collection
            collection_lines = [line]
            open_brackets = stripped.count('(') + stripped.count('[') + stripped.count('{')
            close_brackets = stripped.count(')') + stripped.count(']') + stripped.count('}')
            bracket_balance = open_brackets - close_brackets
            
            j = i + 1
            while j < len(non_imports) and bracket_balance > 0:
                next_line = non_imports[j].strip()
                if not next_line:
                    j += 1
                    continue
                    
                open_brackets = next_line.count('(') + next_line.count('[') + next_line.count('{')
                close_brackets = next_line.count(')') + next_line.count(']') + next_line.count('}')
                bracket_balance += open_brackets - close_brackets
                
                # If it's an indented line in a collection, flatten it
                # Remove leading whitespace and add to the collection
                collection_lines.append(non_imports[j].strip())
                j += 1
                
            # Join the collection as one line to avoid indentation issues
            collection_text = ' '.join(collection_lines)
            result.append(SendingStep.command(collection_text))
            i = j
        
        # Handle normal Python blocks with indentation
        elif line.rstrip().endswith(':'):  # Start of a block like if/for/def/class
            # This is the start of an indented block
            indentation_level = len(line) - len(line.lstrip())
            result.append(SendingStep.command(line, wait_for_prompt=False))
            
            # Process the indented lines in this block
            j = i + 1
            while j < len(non_imports):
                next_line = non_imports[j]
                next_stripped = next_line.strip()
                
                if not next_stripped:  # Empty line
                    j += 1
                    continue
                    
                next_indent = len(next_line) - len(next_line.lstrip())
                
                if next_indent <= indentation_level and next_stripped:
                    # End of the block
                    break
                
                # Send the indented line
                result.append(SendingStep.command(next_line, wait_for_prompt=False))
                j += 1
                
            # At the end of a block, add an empty line to execute it
            result.append(SendingStep.command('', wait_for_prompt=True))
            i = j
        
        # Normal line (not a block or collection)
        else:
            result.append(SendingStep.command(line))
            i += 1
    
    return result
