"""Command line interface for repot."""

import argparse
import sys
import typing as T

from repot.core import send
from repot.targets.interface import TARGETS
from repot.targets.tmux import TmuxConfig


def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="repot",
        description="Send text to a REPL in tmux",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Send command
    send_parser = subparsers.add_parser(
        "send", help="Send text to a REPL in a tmux pane"
    )
    send_parser.add_argument(
        "text",
        nargs="?",
        default="-",
        help="Text to send. Use '-' to read from stdin (default: -)"
    )
    
    # REPL type option
    send_parser.add_argument(
        "--py",
        action="store_true",
        required=True,
        help="Send to Python REPL (python, ptpython, or ipython)"
    )
    
    # Additional options (mutually exclusive)
    mode_group = send_parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--no-bpaste",
        action="store_true",
        help="Disable bracketed paste mode (required for Python < 3.13)"
    )
    mode_group.add_argument(
        "--ipy-cpaste",
        action="store_true",
        help="Use IPython's %%cpaste command (IPython only)"
    )
    # 
    # Connect command (placeholder for future implementation)
    connect_parser = subparsers.add_parser(
        "connect", help="Connect to a specific tmux pane (not implemented yet)"
    )

    return parser


def send_command(text: str, args: argparse.Namespace) -> int:
    """Execute the send command.

    Args:
        text: The text to send to the REPL.
        args: Command line arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Determine language configuration based on args
    language = 'python'  # We only support Python for now
    
    # Check bracketed paste option
    use_bracketed_paste = not args.no_bpaste
    
    language_config: dict[str, T.Any] = {
        'use_cpaste': args.ipy_cpaste,
        'ipython_pause': 100,  # 100ms pause for cpaste by default
        'use_bracketed_paste': use_bracketed_paste,  # Pass the bracketed paste preference to language
    }
    
    # Create target configuration
    try:
        # For now, we only support tmux
        target = 'tmux'
        
        # Get the target config using the target's config method
        target_impl = TARGETS[target]
        target_config = target_impl.config()
        
        # Update config with bracketed paste preference
        if isinstance(target_config, TmuxConfig):
            target_config.use_bracketed_paste = use_bracketed_paste
        
        # Send the text
        send(text, target, target_config, language, language_config)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def connect_command() -> int:
    """Execute the connect command (placeholder).
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    print("Connect command is not implemented yet.")
    print("Currently, repot always sends to the pane to the right.")
    return 0


def main(argv: T.Optional[list[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.command == "send":
        text = args.text
        if text == "-":
            # Read from stdin
            text = sys.stdin.read()

        return send_command(text, args)
    elif args.command == "connect":
        return connect_command()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
