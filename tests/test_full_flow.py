"""Test the full flow from input to tmux."""

import pytest
from repot.languages.python import PythonLanguage
from repot.targets.tmux import TmuxTarget, TmuxConfig


def test_python_class_non_bracketed():
    """Test the full flow for Python class without bracketed paste."""
    input_text = """class Person:
    name: str
    age: int
    address: str

    def get_name(self) -> str:
        return self.name"""
    
    # Language processing
    language_config = {
        'use_bracketed_paste': False,  # Python 3.12 mode
    }
    pieces = PythonLanguage.escape_text(input_text, language_config)
    
    # Should have only one text piece
    assert len(pieces) == 1
    assert pieces[0].type.name == 'TEXT'
    
    processed_text = pieces[0].content
    print("\nProcessed text:")
    print(repr(processed_text))
    
    # Check that blank line was removed
    lines = processed_text.split('\n')
    for i, line in enumerate(lines):
        print(f"Line {i}: {repr(line)}")
    
    # Verify no blank lines between class attributes and method
    assert all(line.strip() != '' or i == len(lines) - 1 for i, line in enumerate(lines))
    
    # What tmux receives (now unmodified for non-bracketed paste)
    tmux_text = processed_text
    print("\nWhat tmux receives:")
    print(repr(tmux_text))
    
    # For non-bracketed paste, text is sent as-is
    print("\nFor non-bracketed paste mode:")
    print("- Text is sent exactly as received from language processor")
    print("- No trailing newline stripping")
    print("- No separate Enter key sent")


