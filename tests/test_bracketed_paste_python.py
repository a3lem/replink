"""Test Python handling with bracketed paste mode."""

import pytest
from repot.languages.python import PythonLanguage


def test_bracketed_paste_simple_statement():
    """Test simple statement with bracketed paste."""
    code = "x = 42"
    
    config = {'use_bracketed_paste': True}
    pieces = PythonLanguage.escape_text(code, config)
    
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should have preprocessing applied (1 newline for simple statement)
    assert result == "x = 42\n"


def test_bracketed_paste_indented_block():
    """Test indented block with bracketed paste."""
    code = """def hello():
    print("hi")"""
    
    config = {'use_bracketed_paste': True}
    pieces = PythonLanguage.escape_text(code, config)
    
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should have preprocessing applied (2 newlines for indented last line)
    assert result == 'def hello():\n    print("hi")\n\n'


def test_bracketed_paste_class_with_blank_lines():
    """Test class definition with blank lines removed."""
    code = """class Person:
    name: str
    
    def __init__(self):
        self.name = "test\""""
    
    config = {'use_bracketed_paste': True}
    pieces = PythonLanguage.escape_text(code, config)
    
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Blank lines should be removed, ends with 2 newlines
    lines = result.split('\n')
    # Check no blank lines in the middle
    for i, line in enumerate(lines[:-2]):  # Exclude trailing newlines
        if i > 0:  # Skip first line
            assert line.strip() != '' or i == len(lines) - 3  # Allow last line before trailing newlines
    
    assert result.endswith('\n\n')


def test_bracketed_paste_multiline_literal():
    """Test multiline literal with bracketed paste."""
    code = """data = {
    'key1': 'value1',
    'key2': 'value2'
}"""
    
    config = {'use_bracketed_paste': True}
    pieces = PythonLanguage.escape_text(code, config)
    
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should have 1 newline (simple statement)
    assert result.endswith('\n')
    assert not result.endswith('\n\n')


def test_bracketed_paste_elif_handling():
    """Test that elif/else blocks stay together."""
    code = """if x > 0:
    print("positive")
elif x < 0:
    print("negative")
else:
    print("zero")"""
    
    config = {'use_bracketed_paste': True}
    pieces = PythonLanguage.escape_text(code, config)
    
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Check that elif/else are not separated by blank lines
    lines = result.strip().split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith(('elif', 'else')):
            # Previous line should not be empty
            assert i > 0 and lines[i-1].strip() != ''
    
    # Should end with 2 newlines (indented last line)
    assert result.endswith('\n\n')


def test_ipython_cpaste_not_affected():
    """Test that IPython %cpaste mode is not affected by preprocessing."""
    code = """class Test:
    
    def method(self):
        pass"""
    
    config = {
        'use_ipython': True,
        'use_cpaste': True,
        'use_bracketed_paste': True
    }
    
    pieces = PythonLanguage.escape_text(code, config)
    
    # Should use %cpaste, not preprocessing
    assert len(pieces) == 4
    assert pieces[0].content == "%cpaste -q\n"
    assert pieces[2].content == code  # Original code unchanged
    assert pieces[3].content == "--\n"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])