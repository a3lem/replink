# About

This is a simple CLI (called 'repot') that editors can use to send text to a Python REPL (aka console) running in a tmux pane on the right.
Both Python and iPython REPLs are supported.

The CLI exposes two commands.

1. Connect: Used to connect the editor to the target pane. In a more fleshed-out implementation, connect might
   set an environment variable that connects a given buffer to the target REPL. Or it might use a jupytre kernel.
   For now let's keep things simple and skip the 'connect' command. Instead, let's assume the REPL is always in the next
   TMUX pane on the right.

2. Send: This essentially navigates to the target pane (if sending directly isn't supported) and pastes the command's
   first argument (a string) inside the console. If the argument is '-' then send/paste STDIN.

# Assumptions

The CLI is implemented in Python (3.12). Use uv (by astral.sh) for python, venv, and depdendency management.

This CLI is designed in the first place to be called from the Helix editor, which neither has builtin repl
support nor exposes a plugin API. Helix is running in a TMUX pane.

Using a helix keybind, the CLI will be called as `:pipe-to repot send -`, where `-` indicates that input is coming from STDIN.

The REPL is running in a TMUX pane immediately to the right.

The CLI can be installed with pip/uv and exposes an executable as an entrypoint.

# Challenges

REPLs/consoles differ in how they expect to receive pasted input. Bracketed pasting is important in some cases.
Look up the code of related projects such as vim-slime.vim to learn how they deal with this.

Here's what you can assume about python REPLs:

- Python <= 3.12 - No support for bracketed paste. Translate vimscript logic at https://github.com/jpalardy/vim-slime/blob/main/ftplugin/python/slime.vim
- Python = 3.13  - Bracketed paste supported.
- iPython - bracketed paste supported
- ptpython - bracketed paste supported.

Not only sending code is important, but also executing it. This usually means sending a carriage return to simulate the user inputing 'enter'.

# Implementation Details

## REPL Detection

- The tool detects whether the target pane is running IPython or standard Python REPL.
- For IPython, it checks for specific patterns like "in [", "ipython", or "%cpaste" in the pane content.
- For standard Python, it checks the pane's command name.

## Code Handling

1. **Text Preprocessing**:
   - Common indentation is detected and removed
   - Extra blank lines are normalized

2. **Standard Python REPL Strategy**:
   - Multiline code (especially functions with indentation) is sent line-by-line
   - Code is intelligently split into "definition blocks" and "execution blocks"
   - Each block is sent separately with appropriate delays
   - Special handling ensures proper indentation and syntax

3. **IPython REPL Strategy**:
   - Uses %cpaste magic command
   - Sends code line-by-line within the paste mode
   - Properly terminates with "--" on a separate line
   - Uses Ctrl+D as a fallback to ensure termination

4. **Single Line Strategy**:
   - Uses bracketed paste mode for proper terminal handling
   - Falls back to buffer-based methods for longer text

## Command Line Options

- `--ipython`: Force IPython mode (%cpaste)
- `--python`: Force standard Python REPL mode
- `--no-bracketed-paste`: Disable bracketed paste mode

# Related Projects

- vim-slime.vim (https://github.com/jpalardy/vim-slime)
- iron.nvim (https://github.com/Vigemus/iron.nvim)

# Developer Guidelines

Use type hints.
