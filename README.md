# replink

A CLI tool for sending code from your editor to a REPL running in tmux.

```text
[>_] -> [>_]
```

## Features

- **Python REPL support**: Works with standard Python, IPython, and ptpython
- **Smart formatting**: Handles indentation, blank lines, and bracketed paste modes
- **Tmux integration**: Send to any tmux pane with simple configuration
- **Editor agnostic**: Works with any editor that can pipe text to commands

## Quick Start

1. Install replink:
   ```bash
   uv tool install replink
   ```

2. Start a Python REPL in a tmux pane:
   ```bash
   python3  # or ipython, ptpython
   ```

3. Send code from your editor or command line:
   ```bash
   # From command line
   echo 'print("hello world")' | replink send -l python -t tmux:p=right
   
   # From file
   replink send -l python -t tmux:p=1 'x = 42\nprint(x)'
   ```

## Installation

### Using uv (recommended)
```bash
uv tool install replink
```

### Using pip
```bash
pip install replink
```

### From source
```bash
git clone https://github.com/yourusername/replink.git
cd replink
uv pip install -e .
```

## Usage

### Basic Syntax
```bash
replink send -l LANGUAGE -t TARGET [OPTIONS] [TEXT]
```

### Examples

**Send to pane on the right:**
```bash
cat script.py | replink send -l python -t tmux:p=right
```

**Send to specific pane:**
```bash
replink send -l python -t tmux:p=1 'print("hello")'
```

**Python < 3.13 (no bracketed paste):**
```bash
cat script.py | replink send -l python -t tmux:p=right --no-bpaste
```

**IPython with %cpaste:**
```bash
cat script.py | replink send -l python -t tmux:p=right --ipy-cpaste
```

### Options

- `-l, --lang`: Language (currently only `python`)
- `-t, --target`: Target configuration (e.g., `tmux:p=right`, `tmux:p=1`)
- `-N, --no-bpaste`: Disable bracketed paste (for Python < 3.13)
- `--ipy-cpaste`: Use IPython's %cpaste command

## Editor Integration

### Helix

Add to your `~/.config/helix/config.toml`:

```toml
[keys.normal]
"<space>x" = ":pipe-to replink send -l python -t tmux:p=right"

[keys.select]
"<space>x" = ":pipe-to replink send -l python -t tmux:p=right"
```

Now you can select code and press `<space>x` to send it to your Python REPL.

### Vim/Neovim

```vim
" Send current line
nnoremap <leader>x :.!replink send -l python -t tmux:p=right<CR>
" Send visual selection
vnoremap <leader>x :!replink send -l python -t tmux:p=right<CR>
```

### VS Code

Create a task in `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Send to REPL",
            "type": "shell",
            "command": "replink",
            "args": ["send", "-l", "python", "-t", "tmux:p=right", "${selectedText}"]
        }
    ]
}
```

## Why replink?

Sending code to a REPL seems simple, but getting the formatting right is surprisingly difficult. Python's significant whitespace, multiple REPL types, and varying bracketed paste support create numerous edge cases.

replink solves this by:

- **Handling Python quirks**: Removes problematic blank lines for older Python versions
- **Smart indentation**: Properly dedents and formats code blocks
- **REPL awareness**: Adapts behavior based on bracketed paste support
- **Following vim-slime**: Uses the battle-tested approach from vim-slime

## How it Works

1. **Language processing**: Python code is analyzed and formatted based on the target REPL's capabilities
2. **Target delivery**: Formatted code is sent to the specified tmux pane
3. **Execution**: A final Enter key executes the code in the REPL

For Python specifically:
- **Python >= 3.13**: Uses bracketed paste, preserves blank lines
- **Python < 3.13**: Removes blank lines, adds smart newlines between code blocks
- **IPython**: Can use bracketed paste or %cpaste for complex code
- **ptpython**: Uses bracketed paste

## Limitations

- **Languages**: Currently only supports Python (more languages planned)
- **Targets**: Currently only supports tmux (screen, terminal apps planned)
- **Dependencies**: Requires tmux to be installed and running

## Acknowledgments

- **[vim-slime](https://github.com/jpalardy/vim-slime)**: The reference implementation for REPL integration
- **[iron.nvim](https://github.com/Vigemus/iron.nvim)**: Additional inspiration for REPL tooling

## License

Licensed under the MIT License. See [LICENSE.txt](LICENSE.txt) for details.
