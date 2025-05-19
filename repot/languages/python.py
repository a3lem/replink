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
    
    For Python < 3.13, we adopt a simpler and more reliable approach:
    1. Use %cpaste-like behavior by flattening the entire code block
    2. Fix indentation and spacing to ensure it's valid Python
    3. Handle special cases like class definitions and multi-line collections
    
    Args:
        text: The Python code to preprocess.
        
    Returns:
        A list of steps to send the code.
    """
    # For Python < 3.13, we have serious limitations with the REPL
    # The most reliable approach is to emulate how %cpaste works in IPython
    # by joining related code blocks together
    
    # First, detect if this code has class definitions or nested blocks
    has_class_def = re.search(r'^\s*class\s+\w+', text, re.MULTILINE) is not None
    has_method_defs = re.search(r'^\s+def\s+\w+', text, re.MULTILINE) is not None
    
    # If we have a class definition with methods, we need special handling
    if has_class_def and has_method_defs:
        return _handle_class_definitions(text)
    
    # For multi-line collections, we need special handling
    has_multiline_collection = (
        re.search(r'^\s*\w+\s*=\s*[\[\{\(]', text, re.MULTILINE) is not None and
        re.search(r'^\s*[\]\}\)]', text, re.MULTILINE) is not None
    )
    
    if has_multiline_collection:
        return _handle_multiline_collections(text)
    
    # For other code, fall back to simple line-by-line processing
    return _basic_line_processing(text)


def _handle_class_definitions(text: str) -> List[Dict[str, Any]]:
    """Handle class definitions for Python < 3.13.
    
    Class definitions with methods need special treatment in Python REPLs.
    We need to ensure:
    1. The class line and each method have the correct indentation
    2. Each method is sent properly indented
    3. An empty line is sent after the class to finalize it
    
    Args:
        text: The Python code containing class definitions.
        
    Returns:
        A list of steps to send the code.
    """
    result = []
    lines = text.splitlines()
    
    # First, find import statements and process them first
    imports = []
    for line in lines:
        if line.strip().startswith(('import ', 'from ')):
            imports.append(line)
    
    for imp in imports:
        result.append(SendingStep.command(imp))
    
    # Now identify and process class definitions
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines and imports
        if not stripped or stripped.startswith(('import ', 'from ')):
            i += 1
            continue
        
        # Check if this is a class definition
        if stripped.startswith('class ') and stripped.endswith(':'):
            # Send the class definition line
            result.append(SendingStep.command(line, wait_for_prompt=False))
            
            # Calculate the indentation level for this class
            class_indent = len(line) - len(line.lstrip())
            expected_method_indent = class_indent + 4  # Standard Python indentation
            
            # Process the class body
            j = i + 1
            while j < len(lines):
                method_line = lines[j]
                method_stripped = method_line.strip()
                
                # Skip empty lines
                if not method_stripped:
                    j += 1
                    continue
                
                # Calculate this line's indentation
                line_indent = len(method_line) - len(method_line.lstrip())
                
                # Check if we're still in the class definition
                if line_indent <= class_indent:
                    # We've exited the class definition
                    break
                
                # For method definitions, ensure correct indentation
                if method_stripped.startswith('def '):
                    # Send method definition with proper indentation
                    result.append(SendingStep.command(' ' * 4 + method_stripped, wait_for_prompt=False))
                    
                    # Look ahead for the method body 
                    method_indent = line_indent
                    k = j + 1
                    
                    while k < len(lines):
                        body_line = lines[k]
                        body_stripped = body_line.strip()
                        
                        # Skip empty lines in method body
                        if not body_stripped:
                            k += 1
                            continue
                            
                        body_indent = len(body_line) - len(body_line.lstrip())
                        
                        # Check if still in method body
                        if body_indent <= method_indent:
                            # Exited method body
                            break
                            
                        # Send method body line with proper indentation (relative to method def)
                        relative_indent = body_indent - method_indent
                        result.append(SendingStep.command(' ' * (4 + relative_indent) + body_stripped, wait_for_prompt=False))
                        k += 1
                        
                    j = k
                    continue
                else:
                    # Regular class attribute or statement
                    result.append(SendingStep.command(' ' * 4 + method_stripped, wait_for_prompt=False))
                    j += 1
            
            # Add empty line to finalize class definition
            result.append(SendingStep.command('', wait_for_prompt=True))
            i = j
            continue
            
        # Handle non-class code
        elif stripped.endswith(':'):  # Other block statements
            result.append(SendingStep.command(line, wait_for_prompt=False))
            block_indent = len(line) - len(line.lstrip())
            
            # Process block body
            j = i + 1
            while j < len(lines):
                block_line = lines[j]
                block_stripped = block_line.strip()
                
                if not block_stripped:
                    j += 1
                    continue
                    
                block_line_indent = len(block_line) - len(block_line.lstrip())
                
                if block_line_indent <= block_indent:
                    # Exited the block
                    break
                    
                result.append(SendingStep.command(block_line, wait_for_prompt=False))
                j += 1
                
            # Add empty line to finalize the block
            result.append(SendingStep.command('', wait_for_prompt=True))
            i = j
            continue
            
        else:
            # Regular statements
            result.append(SendingStep.command(line))
            i += 1
    
    # Ensure we have a final execution line
    if result and not result[-1].get('wait_for_prompt', False):
        result.append(SendingStep.command('', wait_for_prompt=True))
        
    return result


def _handle_multiline_collections(text: str) -> List[Dict[str, Any]]:
    """Handle multi-line collections for Python < 3.13.
    
    Collections like lists, dicts, and tuples need to be flattened for the REPL.
    
    Args:
        text: The Python code containing multi-line collections.
        
    Returns:
        A list of steps to send the code.
    """
    result = []
    lines = text.splitlines()
    
    # First, find import statements and process them first
    imports = []
    non_imports = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('import ', 'from ')):
            imports.append(line)
        elif stripped:  # Skip empty lines
            non_imports.append(line)
    
    # Process imports
    for imp in imports:
        result.append(SendingStep.command(imp))
    
    # Process multi-line collections and other statements
    i = 0
    while i < len(non_imports):
        line = non_imports[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
            
        # Detect the start of a collection assignment
        assignment_match = re.match(r'^(\s*\w+\s*=\s*)([\[\{\(])', stripped)
        
        if assignment_match and not (stripped.endswith(']') or 
                                     stripped.endswith('}') or 
                                     stripped.endswith(')')):
            # This is a multi-line collection assignment
            variable_prefix = assignment_match.group(1)
            collection_start = assignment_match.group(2)
            
            collection_lines = [stripped]  # Start with just the stripped version
            
            # Define corresponding closing bracket
            collection_end = {
                '[': ']',
                '{': '}',
                '(': ')'
            }[collection_start]
            
            # Track bracket balance
            balance = 1  # Starting with one opening bracket
            
            # Find all lines in the collection
            j = i + 1
            while j < len(non_imports) and balance > 0:
                next_line = non_imports[j].strip()
                
                if not next_line:
                    j += 1
                    continue
                    
                collection_lines.append(next_line)
                
                # Update bracket balance
                balance += next_line.count(collection_start) - next_line.count(collection_end)
                j += 1
            
            # Flatten the collection into a single line
            joined_items = []
            for idx, item in enumerate(collection_lines):
                if idx == 0:
                    # Keep the variable assignment intact
                    joined_items.append(item)
                else:
                    # Remove any indentation and join
                    joined_items.append(item.strip())
            
            # Join everything into a single line
            flattened = ' '.join(joined_items)
            
            # Clean up the formatting
            flattened = re.sub(r'\s+', ' ', flattened)  # Remove duplicate spaces
            flattened = re.sub(r',\s*', ', ', flattened)  # Ensure space after commas
            
            # Send as a single command
            result.append(SendingStep.command(flattened))
            i = j
            continue
            
        # Handle other statements
        else:
            result.append(SendingStep.command(line))
            i += 1
    
    # Ensure there's at least one wait_for_prompt=True
    has_waiting_prompt = False
    for step in result:
        if step.get('wait_for_prompt', False):
            has_waiting_prompt = True
            break
            
    if not has_waiting_prompt and result:
        last_step = result[-1].copy()
        last_step['wait_for_prompt'] = True
        result[-1] = last_step
            
    return result


def _basic_line_processing(text: str) -> List[Dict[str, Any]]:
    """Basic line-by-line processing for simple code blocks.
    
    Args:
        text: The Python code to process line by line.
        
    Returns:
        A list of steps to send the code.
    """
    result = []
    lines = [line for line in text.splitlines() if line.strip()]
    
    # Track indentation state
    in_block = False
    block_indent = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
            
        # Calculate indent level
        indent = len(line) - len(line.lstrip())
        
        # Check for block start
        if stripped.endswith(':'):
            in_block = True
            block_indent = indent
            result.append(SendingStep.command(line, wait_for_prompt=False))
            continue
            
        # Check if in a block
        if in_block:
            if indent > block_indent:
                # Still in the block
                result.append(SendingStep.command(line, wait_for_prompt=False))
            else:
                # Exited the block
                result.append(SendingStep.command('', wait_for_prompt=True))
                in_block = False
                result.append(SendingStep.command(line))
        else:
            # Regular statement outside a block
            result.append(SendingStep.command(line))
    
    # Close any open blocks at the end
    if in_block:
        result.append(SendingStep.command('', wait_for_prompt=True))
        
    # Ensure there's at least one wait_for_prompt=True
    has_waiting_prompt = False
    for step in result:
        if step.get('wait_for_prompt', False):
            has_waiting_prompt = True
            break
            
    if not has_waiting_prompt and result:
        last_step = result[-1].copy()
        last_step['wait_for_prompt'] = True
        result[-1] = last_step
            
    return result
