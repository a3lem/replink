# repot

*Read Eval Print Over There*

A simple CLI to send text from Helix to a Python REPL running in a tmux pane, with proper handling of indentation and multiline code.

## Installation

```bash
# Using pip
pip install repot

# Using uv
uv pip install repot
```

For development installation:

```bash
# Clone the repository
git clone https://github.com/yourusername/repot.git
cd repot

# Install in development mode
uv pip install -e .
```

## Usage

repot is designed to be used from Helix editor running in a tmux pane, with a Python REPL running in an adjacent pane.

### Send text to REPL

To send text to the Python REPL in the pane to the right:

```bash
repot send "print('Hello, world!')"
```

Read from stdin (useful for piping from Helix):

```bash
echo "print('Hello, world!')" | repot send -
```

### Advanced Options

repot supports several options for handling different REPL environments:

```bash
# Force IPython mode (uses %cpaste for multiline code)
repot send --ipython "def hello():\n    print('world')"

# Force standard Python mode (no %cpaste)
repot send --python "def hello():\n    print('world')"

# Disable bracketed paste mode
repot send --no-bracketed-paste "print('Hello')"
```

### Helix Configuration

Add this to your `~/.config/helix/config.toml`:

```toml
[keys.normal]
S = [":pipe-to repot send -", "collapse_selection"]
```

With this configuration, you can:

1. Select some text in Helix
2. Press `S` to send it to the Python REPL in the pane to the right

## Features

- Automatic detection of Python and IPython REPLs
- Intelligent handling of multiline code blocks
- Automatic dedentation of code blocks
- Special handling for IPython using %cpaste
- Support for bracketed paste mode
- Efficient handling of large code blocks

## How It Works

repot:

1. Determines the tmux pane to the right of the current pane
2. Automatically detects if it's running a Python or IPython REPL
3. Preprocesses the code (removes extra blank lines, dedents code blocks)
4. For IPython with multiline code, uses the `%cpaste` magic command
5. For other cases, uses tmux's bracketed paste or buffer methods depending on size

## Limitations

- Currently only supports sending to the pane to the right
- The "connect" command is not yet implemented
- Limited error handling for complex tmux setups

## License

MIT
