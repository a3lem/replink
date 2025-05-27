#!/usr/bin/env python3
import re

def vim_slime_escape(text):
    """Mimics vim-slime's _EscapeText_python function"""
    # 1. Remove consecutive empty lines
    empty_lines_pat = r'(^|\n)(\s*\n)+'
    no_empty_lines = re.sub(empty_lines_pat, r'\1', text)
    
    # 2. Find common indentation from the first line
    first_indent_match = re.match(r'^\s*', no_empty_lines)
    common_indent = first_indent_match.group(0) if first_indent_match else ""
    
    # 3. Remove common indentation from all lines
    if common_indent:
        dedent_pat = r'(^|\n)' + re.escape(common_indent)
        dedented_lines = re.sub(dedent_pat, r'\1', no_empty_lines)
    else:
        dedented_lines = no_empty_lines
    
    # 4. Add extra newline before lines that don't start with elif/else/except/finally
    # This regex matches: newline + spaces + non-newline chars + newline
    # followed by (not elif/else/except/finally) + non-whitespace OR end of string
    add_eol_pat = r'\n\s[^\n]+\n(?=(?:(?!elif|else|except|finally)\S|$))'
    result = re.sub(add_eol_pat, lambda m: m.group(0) + '\n', dedented_lines)
    
    return result

# Read the test file
with open('tests/data/python.txt', 'r') as f:
    text = f.read()

# Apply escape
escaped = vim_slime_escape(text)

print("=== ORIGINAL ===")
print(repr(text))
print("\n=== ESCAPED ===")
print(repr(escaped))

# Save escaped output
with open('debug_escaped.txt', 'w') as f:
    f.write(escaped)