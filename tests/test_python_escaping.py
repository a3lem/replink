"""Test Python code escaping for REPL."""

import pytest
from repot.languages.python import prepare_python_blocks


def test_class_with_blank_lines():
    """Test that blank lines are removed from class definitions."""
    input_code = """class Person:
    name: str
    age: int
    address: str

    def get_name(self) -> str:
        return self.name"""
    
    expected_output = """class Person:
    name: str
    age: int
    address: str
    def get_name(self) -> str:
        return self.name
"""
    
    result_pieces = prepare_python_blocks(input_code)
    actual_output = result_pieces[0].content
    
    assert actual_output == expected_output


def test_multiple_blank_lines():
    """Test that multiple consecutive blank lines are removed."""
    input_code = """def foo():
    pass


def bar():
    pass"""
    
    expected_output = """def foo():
    pass
def bar():
    pass
"""
    
    result_pieces = prepare_python_blocks(input_code)
    actual_output = result_pieces[0].content
    
    assert actual_output == expected_output


def test_indented_class():
    """Test class with common indentation."""
    input_code = """    class Person:
        name: str
        
        def get_name(self) -> str:
            return self.name"""
    
    expected_output = """class Person:
    name: str
    def get_name(self) -> str:
        return self.name
"""
    
    result_pieces = prepare_python_blocks(input_code)
    actual_output = result_pieces[0].content
    
    assert actual_output == expected_output