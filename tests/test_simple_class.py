"""Test with a simple class definition."""

import subprocess
import sys
from repot.languages.python import prepare_python_blocks

# Simple test case
test_code = """class Person:
    name: str
    age: int

    def get_name(self) -> str:
        return self.name"""

print("Original code:")
print(test_code)
print("\n" + "="*50 + "\n")

# Process with prepare_python_blocks
result_pieces = prepare_python_blocks(test_code)
processed = result_pieces[0].content

print("Processed code:")
print(processed)
print("\n" + "="*50 + "\n")

print("Processed code (repr):")
print(repr(processed))
print("\n" + "="*50 + "\n")

# Write to a temp file to send
with open('/tmp/test_python_code.txt', 'w') as f:
    f.write(test_code)

print("To test with repot:")
print("cat /tmp/test_python_code.txt | repot send --py --no-bpaste")