"""Python REPL handler module.

This module provides utilities for processing and sending Python code to different REPL types:

- Standard Python < 3.13: No bracketed paste support, needs special handling
- Standard Python >= 3.13: Has bracketed paste support
- IPython: Uses bracketed paste
- ptpython: Uses bracketed paste
"""

import re


def preprocess_code(text: str) -> str:
    """Preprocess Python code for sending to any REPL.
    
    This performs basic preprocessing that's appropriate for all REPL types.
    For Python < 3.13 without bracketed paste, use preprocess_for_line_mode
    after calling this function.
    
    Args:
        text: The Python code to preprocess.
        
    Returns:
        Preprocessed code ready for pasting.
    """
    import textwrap
    
    # Remove extra blank lines (more than one consecutive)
    text = re.sub(r'(^|\n)\s*\n+', '\n', text)
    
    # Use textwrap.dedent to properly handle Python's indentation
    text = textwrap.dedent(text)
    
    # Ensure the text ends with a single newline
    text = text.rstrip() + '\n'
    
    return text


def preprocess_for_line_mode(text: str) -> list:
    """Preprocess Python code for line-by-line sending to Python < 3.13.
    
    This function transforms multi-line code into a series of lines that can be 
    sent one-by-one to a Python REPL that doesn't support bracketed paste.
    It handles significant whitespace and ensures proper execution of blocks.
    
    Args:
        text: The Python code to preprocess (should already be run through preprocess_code).
        
    Returns:
        A list of dictionaries with 'line' and 'wait_for_prompt' keys, ready for sending.
    """
    import textwrap
    
    # Split into groups based on syntax
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
            result.append({
                'line': imp,
                'wait_for_prompt': True
            })
    
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
            result.append({
                'line': collection_text,
                'wait_for_prompt': True
            })
            i = j
        
        # Handle normal Python blocks with indentation
        elif line.rstrip().endswith(':'):  # Start of a block like if/for/def/class
            # This is the start of an indented block
            indentation_level = len(line) - len(line.lstrip())
            result.append({
                'line': line,
                'wait_for_prompt': False  # Don't wait for prompt after starting a block
            })
            
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
                result.append({
                    'line': next_line,
                    'wait_for_prompt': False  # Don't wait inside a block
                })
                j += 1
                
            # At the end of a block, add an empty line to execute it
            result.append({
                'line': '',
                'wait_for_prompt': True  # Wait after executing a block
            })
            i = j
        
        # Normal line (not a block or collection)
        else:
            result.append({
                'line': line,
                'wait_for_prompt': True
            })
            i += 1
    
    return result


def format_for_cpaste(text: str) -> list:
    """Format text for sending to IPython with %cpaste command.
    
    This enables reliable pasting of multi-line code in IPython.
    
    Args:
        text: The Python code to send.
        
    Returns:
        A list of steps to execute the code using %cpaste.
    """
    return [
        {
            'type': 'command',
            'content': '%cpaste -q',
            'wait_for_prompt': False
        },
        {
            'type': 'delay',
            'content': 0.1
        },
        {
            'type': 'text',
            'content': text,
            'wait_for_prompt': False
        },
        {
            'type': 'command',
            'content': '--',
            'wait_for_prompt': True
        }
    ]


def detect_block_structure(text: str) -> list:
    """Detect the indentation structure of a Python code block.
    
    This is particularly useful for Python < 3.13 when not using bracketed paste.
    
    Args:
        text: The Python code to analyze.
        
    Returns:
        A list of blocks with their indentation levels and content.
    """
    lines = text.splitlines()
    blocks = []
    current_block = []
    current_indent = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:  # Empty line
            continue
            
        indent = len(line) - len(line.lstrip())
        
        # Start of a new block or continuing an existing one?
        if current_block and indent > current_indent:
            # Continuing a block with increased indentation
            current_block.append(line)
        elif current_block and indent == current_indent:
            # Continuing a block at the same level
            current_block.append(line)
        else:
            # Start a new block
            if current_block:
                blocks.append({
                    'indent': current_indent,
                    'lines': current_block
                })
            current_block = [line]
            current_indent = indent
    
    # Add the last block
    if current_block:
        blocks.append({
            'indent': current_indent,
            'lines': current_block
        })
    
    return blocks