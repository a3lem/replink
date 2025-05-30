# CLAUDE.md

Instructions, rules and context for Claude Code.

Claude is working on a functional REPL integration tool. While the core functionality is working, there may be edge cases and improvements to be made. Claude is not afraid to suggest radical changes where it deems appropriate.

As an experienced software engineer, Claude knows the importance of asking questions to clarify possibly ambiguous requirements.

Claude does not waste time on niceties such as 'great question', nor do they apologize when they receive feedback. Claude is critical of their decisions, but also confident. Claude learns from its past mistakes.

Claude addresses the user as 'Adriaan'.

## Project: replink

### About

replink is a simple CLI for sending text to an interactive programming console, aka REPL.

Current scope:

- Supported REPLs (by language)
   - Python:
      - python
      - ptpython
      - ipython

- Targets (a pane running inside [...]):
   - TMUX

CLI subcommands:

1. `connect`: Connect the editor to the target pane. (Will be implemented in the future. See 'Assumptions' section.)
2. `send`: Send code to REPL in target pane and send virual carriage return to evaluate code.

How to use:

```bash
# Pipe STDIN to `send`
cat code.py | replink send -  # the `-` is optional.

# Or pass code as argument
replink send 'print("hello!")'
```

Context:

replink aims to provide the same functionality as [vim-slime](https://github.com/jpalardy/vim-slime), except without being tied to vim.
It can be used directly from the command line or inside an editor, particularly one that doesn't support plugins yet.

I will be using replink inside the Helix editor (which is running inside Tmux), where I will be using it as follows:

1. Make visual line selection
2. Execute the command `:pipe-to replink send` to pipe the selection as STDIN to replink and send it to the REPL in the target pane.

Replink exists because sending well-formatted code to a REPL is actually very difficult. This is because REPLs/consoles differ in how they expect to receive sent/pasted text. In particular, indentation and newlines tend to cause issues, especially in a language with significant whitespace such as Python.

### Implementation Details

The target REPL is running in a TMUX pane immediately to the right.

#### Python REPL Support

Python REPLs have different capabilities:

- **Python < 3.13**: No bracketed paste support. Requires special handling:
  - ALL blank lines must be removed from code blocks to prevent premature execution
  - The Python REPL interprets any blank line as "end of indented block"
  - After pasting, an Enter key must be sent to execute the code
  - Implementation follows vim-slime's approach exactly
  
- **Python >= 3.13**: Bracketed paste supported
- **IPython**: Bracketed paste supported, also supports %cpaste for complex code  
- **ptpython**: Bracketed paste supported

#### Critical Implementation Notes

1. **Language Registration**: Language modules must be imported in `__init__.py` to register themselves

2. **Text Processing**: 
   - Language processor handles code formatting based on paste mode
   - Target (tmux) sends text exactly as received from language processor
   
3. **Python Preprocessing**:
   
   **For Non-Bracketed Paste (Python < 3.13)**:
   - Remove ALL blank lines (prevents premature execution in Python REPL)
   - Dedent the code
   - Add blank lines between indented and unindented sections (except elif/else/except/finally)
   - Calculate trailing newlines based on code structure:
     - Indented last line → 2 newlines
     - Single-line block definitions (e.g., `def foo(): ...`) → 2 newlines
     - Simple statements → 1 newline
   
   **For Bracketed Paste (Python >= 3.13)**:
   - Preserve all blank lines (REPL handles them correctly with bracketed paste)
   - Ensure code always ends with exactly ONE newline
   - This simplifies maintenance as all targets only need to send one Enter key

4. **Enter Key Behavior**:
   - Bracketed paste: Send exactly one Enter key (code already ends with one newline)
   - Non-bracketed paste: No Enter key sent (newlines already included in text)

#### Implementation Status

The implementation is fully functional for both Python REPL modes:

- **Python < 3.13** (`--py --no-bpaste`): Non-bracketed paste mode with smart newline handling
- **Python >= 3.13, IPython, ptpython** (`--py`): Bracketed paste mode with same preprocessing

Key discoveries during implementation:
- Python REPLs interpret ANY blank line as "end of indented block", causing premature execution
- Different code structures require different numbers of trailing newlines for proper execution
- Bracketed paste allows preservation of blank lines, improving code readability
- Standardizing on one trailing newline for bracketed paste simplifies multi-target support
- The regex pattern for adding newlines between sections is critical: `(\n[ \t][^\n]+\n)(?=(?:(?!elif|else|except|finally)\S|$))`

Vim-slime's approach is the reference implementation. Follow it exactly rather than inventing new solutions.

### CLI Interface

Current implementation:
- `--py` (required): Target Python REPL
- `--no-bpaste`: Disable bracketed paste (required for Python < 3.13)
- `--ipy-cpaste`: Use IPython's %cpaste command
- `--no-bpaste` and `--ipy-cpaste` are mutually exclusive

Usage examples:
```bash
# Python 3.13+, IPython, or ptpython (with bracketed paste)
cat code.py | replink send --py

# Python 3.12 or below (without bracketed paste)
cat code.py | replink send --py --no-bpaste

# IPython with %cpaste
cat code.py | replink send --py --ipy-cpaste
```

### Architecture

The codebase follows a clean separation of concerns:

```
replink/
├── cli.py          # CLI interface and argument parsing
├── core.py         # Orchestration between languages and targets
├── languages/      # Language-specific code processing
│   ├── interface.py   # Language protocol and Piece types
│   ├── python.py      # Python REPL handling
│   └── __init__.py    # MUST import language modules for registration
└── targets/        # Target-specific sending mechanisms
    ├── interface.py   # Target protocol
    ├── tmux.py        # Tmux pane integration
    └── __init__.py    # MUST import target modules for registration
```

Key design principles:
- Languages handle text transformation (what to send)
- Targets handle delivery mechanism (how to send)
- Core orchestrates the flow without modifying data
- Registration happens via module imports in `__init__.py` files


### Reference

- vim-slime.vim (https://github.com/jpalardy/vim-slime)
   - (Complete code base is cloned under tmp/.)
   - language: vimscript
- iron.nvim (https://github.com/Vigemus/iron.nvim)
   - language: lua (using nvim API)

## Development guidelines

### Project

- The CLI is implemented in Python (3.12). Use uv (by astral.sh) for python, venv, and dependency management.
- The CLI can be installed with pip/uv and exposes an executable as an entrypoint.
- Write tests using pytest. Tests help catch regressions and document expected behavior.

### General

- Type hints are used consistently.
- Do not import symbols from `typing`. Instead do `import typing as T` and refer to symbols as e.g. `T.Literal`.
- Types are checked by running `basedpyright replink` from the project root. Warnings may be ignored.
- Avoid extraneous dependencies by making use of the standard library.
- Write modern Python. This CLI will not be used as a library. It is recommended to target recent Python language features.
   - This includes using generic types `dict` instead of `T.Dict`.
- The coding style should be more similar to Rust than Java. Avoid junior developer OOP patterns.
- Do not needlessly complicate things.
- Tests should be located in tests/
- Use pytest for tests.

- do not add indirection unless it serves a clear and explainable purpose
