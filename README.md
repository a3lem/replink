```text
[I_] -> [>_]
```

# 🔗 replink

A very simple CLI tool for sending code to a REPL running in a target pane.

Languages:

- Python

Targets:

- Tmux

## Demo

\[insert ascii cinema\]

## What

It is written in Python and borrows heavily from vim-slime.

## Why

As a Helix user, I often miss an easy way to evaluate blocks of code
interactively. Until Helix's much-discussed plugin API lands, the best approach
is to select code and send it as STDIN (`:pipe-to`) to a shell command that does
the actual work.

Sending code to a REPL is relatively easy. Getting it there in syntactically correct
format, on the other hand, is hard. Or at least, Python makes it hard, with its
handling of identation and newlines, its numerous REPLs (python, ptpython, ipython),
and their varying support for bracketed paste.

I built `replink` so I can send correctly formatted Python code to a TMUX pane.

By open-sourcing it, I hope you can do the same. 

## How To Use


## Limitations

### Languages

- Python
- ...

### Targets

- Tmux
- ...

## Installation

```bash
uv tool install replink
```
### Add to Editor

#### Helix

## Concepts

### Target

### Languages

## Limitations

## Acknowledgements

### Vim-slime

### Claude

