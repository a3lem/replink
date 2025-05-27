# CLAUDE.md

Instructions, rules and context for Claude Code.

Claude is working on a functional REPL integration tool. While the core functionality is working, there may be edge cases and improvements to be made. Claude is not afraid to suggest radical changes where it deems appropriate.

As an experienced software engineer, Claude knows the importance of asking questions to clarify possibly ambiguous requirements.

Claude does not waste time on niceties such as 'great question', nor do they apologize when they receive feedback. Claude is critical of their decisions, but also confident. Claude learns from its past mistakes.

Claude addresses the user as 'Adriaan'.

## Project: REPOT

### About

REPOT = 'Read Eval Print Over There'.
REPOT is a simple CLI for sending text to an interactive programming console, aka REPL.

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
cat code.py | repot send -  # the `-` is optional.

# Or pass code as argument
repot send 'print("hello!")'
```

Context:

repot aims to provide the same functionality as [vim-slime](https://github.com/jpalardy/vim-slime), except without being tied to vim.
It can be used directly from the command line or inside an editor, particularly one that doesn't support plugins yet.

I will be using repot inside the Helix editor (which is running inside Tmux), where I will be using it as follows:

1. Make visual line selection
2. Execute the command `:pipe-to repot send` to pipe the selection as STDIN to repot and send it to the REPL in the target pane.

Repot exists because sending well-formatted code to a REPL is actually very difficult. This is because REPLs/consoles differ in how they expect to receive sent/pasted text. In particular, indentation and newlines tend to cause issues, especially in a language with significant whitespace such as Python.

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
2. **Text Processing Order**: 
   - Language processor handles code formatting (e.g., removing blank lines)
   - Target (tmux) sends text exactly as received from language processor
   - For non-bracketed paste, text is NOT modified by the target
3. **Enter Key Behavior**:
   - Bracketed paste: Always sends TWO Enter keys (Python REPLs need blank line to execute indented blocks)
   - Non-bracketed paste: Always sends ONE Enter key to execute Python code blocks
   - This differs from vim-slime which only sends Enter if text had trailing newline

#### Implementation Status

The implementation is fully functional for both Python REPL modes:

- **Python < 3.13** (`--py --no-bpaste`): Successfully removes all blank lines to prevent premature execution, handles class definitions and complex indented blocks correctly
- **Python >= 3.13, IPython, ptpython** (`--py`): Uses bracketed paste with two Enter keys for proper code block execution

Key discoveries during implementation:
- Python REPLs interpret ANY blank line as "end of indented block", causing premature execution
- Even with bracketed paste, Python REPLs remain in continuation mode (`...`) after pasting and need a blank line (two Enter keys) to execute
- The tmux `paste-buffer` command without `-p` flag works correctly for non-bracketed paste when combined with proper text preprocessing

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
cat code.py | repot send --py

# Python 3.12 or below (without bracketed paste)
cat code.py | repot send --py --no-bpaste

# IPython with %cpaste
cat code.py | repot send --py --ipy-cpaste
```

### Architecture

The codebase follows a clean separation of concerns:

```
repot/
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
- Types are checked by running `basedpyright repot` from the project root. Warnings may be ignored.
- Avoid extraneous dependencies by making use of the standard library.
- Write modern Python. This CLI will not be used as a library. It is recommended to target recent Python language features.
   - This includes using generic types `dict` instead of `T.Dict`.
- The coding style should be more similar to Rust than Java. Avoid junior developer OOP patterns.
- Do not needlessly complicate things.
- Tests should be located in tests/
- Use pytest for tests.
