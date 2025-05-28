"""Test Python newline handling for different code patterns."""

import pytest
from repot.languages.python import prepare_python_blocks


def test_indented_last_line():
    """Test code blocks where the last line is indented."""
    code = """with open(f) as fp:
    data = fp.read()"""
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should end with exactly 2 newlines for indented last line
    assert result.endswith('\n\n')
    assert not result.endswith('\n\n\n')
    

def test_simple_statement():
    """Test simple statements that need only one newline."""
    code = "x = 42"
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should end with exactly 1 newline
    assert result.endswith('\n')
    assert not result.endswith('\n\n')


def test_multiline_literal():
    """Test multiline literals (lists, dicts, etc)."""
    code = """a = [
    'hello',
    'world'
]"""
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should end with exactly 1 newline (it's a simple statement)
    assert result.endswith('\n')
    assert not result.endswith('\n\n')


def test_single_line_function():
    """Test single-line function definitions."""
    code = "def hello(): ..."
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should end with exactly 2 newlines (special case for single-line blocks)
    assert result.endswith('\n\n')
    assert not result.endswith('\n\n\n')


def test_multiline_function():
    """Test multi-line function definitions."""
    code = """def hello():
    print("hi")"""
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should end with exactly 2 newlines (indented last line)
    assert result.endswith('\n\n')
    assert not result.endswith('\n\n\n')


def test_class_definition():
    """Test class definitions."""
    code = """class Foo:
    def __init__(self):
        self.x = 1"""
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should end with exactly 2 newlines (indented last line)
    assert result.endswith('\n\n')
    assert not result.endswith('\n\n\n')


def test_blank_line_removal():
    """Test that blank lines are properly removed."""
    code = """def foo():
    x = 1
    
    y = 2
    
    return x + y"""
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should have no blank lines in the middle
    assert '\n\n' not in result[:-2]  # Exclude the trailing newlines
    # Should still end with 2 newlines (indented last line)
    assert result.endswith('\n\n')


def test_elif_else_handling():
    """Test that elif/else are not separated with extra newlines."""
    code = """if x:
    print("x")
elif y:
    print("y")
else:
    print("z")"""
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # elif and else should not have extra newlines before them
    lines = result.strip().split('\n')
    
    # Find elif and else lines
    for i, line in enumerate(lines):
        if line.strip().startswith(('elif', 'else')):
            # Previous line should not be empty
            assert lines[i-1].strip() != ''
    
    # Should end with 2 newlines (indented last line)
    assert result.endswith('\n\n')


def test_exception_handling():
    """Test that except/finally are not separated with extra newlines."""
    code = """try:
    risky_operation()
except ValueError:
    handle_error()
finally:
    cleanup()"""
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # except and finally should not have extra newlines before them
    lines = result.strip().split('\n')
    
    for i, line in enumerate(lines):
        if line.strip().startswith(('except', 'finally')):
            # Previous line should not be empty
            assert lines[i-1].strip() != ''
    
    # Should end with 2 newlines (indented last line)
    assert result.endswith('\n\n')


def test_mixed_indentation_levels():
    """Test code with multiple indentation levels."""
    code = """def outer():
    def inner():
        for i in range(10):
            if i % 2 == 0:
                print(i)"""
    
    pieces = prepare_python_blocks(code)
    assert len(pieces) == 1
    result = pieces[0].content
    
    # Should end with 2 newlines (indented last line)
    assert result.endswith('\n\n')
    assert not result.endswith('\n\n\n')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])