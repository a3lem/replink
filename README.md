<p align="center">
  <img src="assets/replink_banner.png" alt="replink banner" width="50%">
</p>

# replink

`replink` is a CLI tool for piping code to a REPL running in a different pane and executing it there.

Handy when you want to evaluate code interactively, but your [favorite code editor](https://docs.helix-editor.com/master/) doesn't have a plugin system [(yet)](https://github.com/helix-editor/helix/pull/8675) but can [pipe selected text to a shell command](https://docs.helix-editor.com/commands.html#:~:text=the%20shell%20command.-,%3Apipe%2Dto,-Pipe%20each%20selection)!

## Demo

![Demo GIF](https://github.com/user-attachments/assets/ec7962d4-8401-4f8b-bb68-047879fd3917)

## Why?

`replink` sends code from your editor to a REPL running elsewhere.

**Example**: Python code to an IPython console inside a TMUX pane.

Sound easy enough? The 'sending' part may be, but getting code to show up in the right format on arrival is tricky.

As prior work like [vim-slime](https://github.com/jpalardy/vim-slime) figured out long ago, the solution lies in preprocessing code before sending it and accounting for whether the target expects [bracketed paste](https://cirw.in/blog/bracketed-paste) or not. To make things extra fun, each language and each REPL presents subtle edge cases.

I built `replink` because I got used to sending Python code to a REPL early on in my career -- and Pycharm, VS Code, and Vim have all served to reinforce that habit. If I enjoyed maintaing a (Neo)vim config more, I would just use vim-slime or iron.nvim. But I like [**Helix**](https://docs.helix-editor.com/master/), even if it doesn't have a plugin system. It makes up for it though with its `:pipe-to` command, which lets you send-and-forget selected text as stdin to any shell command -- `replink`, in this case. Tell `replink` what you're sending ('language') and where it needs to go ('target'); bind the complete command to a Helix keybinding, and you nearly have something that feels like a plugin.

## Languages & Targets

`replink` supports these languages and targets:

**Languages & REPLs**:

- Python
    + stock console
        - Tested against various python3 REPLs.
        - For python <= 3.12, use `--no-bpaste/-N`. Python >= 3.13 uses bracketed paste.
    + ipython
        - Special --ipy-cpaste command for `%cpaste` pasting (I rarely need this).
    + ptpython
        - Behaves similarly to python3.13 and above.

**Targets**:

- TMUX

Adding new languages and targets is straightforward. Any language or target available in [vim-slime](https://github.com/jpalardy/vim-slime) can be ported over. This is because `replink`'s architecture borrows heavily from vim-slime.

FRs and PRs welcome!

## Install

### With uv (recommended)

Use python >= 3.12.

```bash
uv tool install --python 3.12 replink
```

## Usage

```bash
replink send -l LANGUAGE -t TARGET [OPTIONS] [TEXT/-]
```

### Options

- `-l, --lang`: Language (currently only `python`)
- `-t, --target`: Target configuration (e.g., `tmux:p=right`, `tmux:p=1`)
- `-N, --no-bpaste`: Disable bracketed paste (for Python < 3.13)
- `--ipy-cpaste`: Use IPython's %cpaste command

### Examples

#### Pipe code in

This is how I usually use replink, except I pipe in whatever is selected in my editor.

```bash
cat script.py | replink send -l python -t tmux:p=right
```

`tmux:p=right` means 'use TMUX and send to the pane on the right of the current pane'. (The value of `p` is anything that can be interpreted by `tmux selectp -t $VALUE`.)

Specifying the TMUX target using the pane number is also valid. (Hitting `<prefix-key> q` shows the pane numbers.)

```bash
echo 'print("well hello there")' | replink send -l python -t tmux:p=4
```

#### Code as an argument

Code can also be passed to `replink` as a positional argument.

```bash
replink send -l python -t tmux:p=right 'print("oh hi!")'
```

I only really use this when I'm debugging, since Python's built-in debugger doesn't play nice with active pipes.

However, it makes the following slightly easier to write:

```bash
replink send -l python -t tmux:p=right 'exit()'
```

#### Python < 3.13 (no bracketed paste):

Up to and including Python 3.12, the standard Python console doesn't support bracketed paste, so make sure to disable it with `--no-bpaste` (or `-N`).

```bash
cat script.py | replink send -l python -t tmux:p=right --no-bpaste
```

## Editor Integration

### Helix

Add to your `~/.config/helix/config.toml`:

```toml
[keys.normal."minus"]
x = ":pipe-to replink send -l python -t tmux:p=right"
```

Now you can select code and press `<minus>x` to send it to your Python REPL. (I use minus/dash (`-`) as my leader for custom keybindings.)


**Pro tip**: If you're building Helix from master, you can specify the language dynamically by passing it in as a [command line expansion](https://docs.helix-editor.com/master/command-line.html#expansions). For example:

```toml
[keys.normal."minus"]
"x" = ":pipe-to replink send -l %{language} -t tmux:p=right"
```

### Vim/Neovim

I'm not sure why you would use `replink` in Vim, where better options exist. But here's what Claude has to say!

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

## Extending replink

Adding languages means implementing the `Language_P` protocol in `replink/languages/`. You handle the formatting quirks and REPL-specific behavior for your language.

Adding targets means implementing the `Target_P` protocol in `replink/targets/`. You handle the mechanics of getting text to wherever the REPL is running.

Right now there's just Python and tmux, but the design should make it straightforward to add JavaScript/Node, Ruby, R, or whatever. Same for targets like GNU Screen, Zellij, or terminal emulators with their own APIs.

## Contributing

PRs welcome, especially for new languages and targets. The architecture should make this pretty straightforward.

## Acknowledgments

Heavily inspired by [vim-slime](https://github.com/jpalardy/vim-slime), which figured out all the hard parts years ago. (I've copied from this project liberally and have opted for the same license.) Also looked at [iron.nvim](https://github.com/Vigemus/iron.nvim) for ideas.


## License

Licensed under the MIT License. See [LICENSE.txt](LICENSE.txt) for details.

