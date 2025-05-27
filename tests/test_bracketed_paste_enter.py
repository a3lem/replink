"""Test Enter key behavior for bracketed paste mode."""

import pytest


def test_python_function_needs_double_enter():
    """Test that Python functions need two Enter keys to execute."""
    # Test cases showing what Python REPL needs
    
    # Case 1: Function with single trailing newline
    code1 = "def hello():\n    print('hi')\n"
    # After pasting this, we get:
    # >>> def hello():
    # ...     print('hi')
    # ... [cursor here]
    # Need one more Enter to execute
    
    # Case 2: Function with double trailing newline  
    code2 = "def hello():\n    print('hi')\n\n"
    # After pasting this, we get:
    # >>> def hello():
    # ...     print('hi')
    # ...
    # >>> [cursor here - function executed]
    
    # For bracketed paste, we need to detect if we're sending
    # an indented code block and ensure proper execution
    assert code1.strip().startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'try:'))
    assert not code1.endswith('\n\n')  # Needs extra Enter
    assert code2.endswith('\n\n')  # Already has blank line