"""Test subprocess text handling to debug tmux issues."""

import subprocess
import pytest


def test_subprocess_text_mode_preserves_newlines():
    """Test that subprocess with text=True preserves our exact newline structure."""
    # Test text that should NOT have blank lines
    test_text = 'class Person:\n    name: str\n    age: int\n    def get_name(self) -> str:\n        return self.name\n'
    
    # Run through subprocess with text=True (as tmux.py does)
    result = subprocess.run(
        ["cat"],
        input=test_text,
        text=True,
        capture_output=True,
        check=True
    )
    
    # Should preserve exact text
    assert result.stdout == test_text
    
    # Verify no blank lines were introduced
    lines = result.stdout.split('\n')
    assert lines[0] == 'class Person:'
    assert lines[1] == '    name: str'
    assert lines[2] == '    age: int'
    assert lines[3] == '    def get_name(self) -> str:'
    assert lines[4] == '        return self.name'
    assert lines[5] == ''  # Final empty line from trailing \n
    assert len(lines) == 6


def test_tmux_load_buffer_simulation():
    """Simulate what should happen with tmux load-buffer."""
    test_text = 'class Person:\n    name: str\n    age: int\n    def get_name(self) -> str:\n        return self.name\n'
    
    # Write to temp file to simulate tmux load-buffer from file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(test_text)
        temp_path = f.name
    
    # Read back
    with open(temp_path, 'r') as f:
        read_back = f.read()
    
    assert read_back == test_text
    
    # Clean up
    import os
    os.unlink(temp_path)