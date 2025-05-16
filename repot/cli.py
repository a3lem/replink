"""Command line interface for repot."""

import argparse
import sys
from typing import List, Optional

from repot import tmux
from repot.repls import python


def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="repot",
        description="Send text from Helix to a Python REPL in tmux",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Send command
    send_parser = subparsers.add_parser(
        "send", help="Send text to a Python REPL in a tmux pane"
    )
    send_parser.add_argument(
        "text",
        nargs="?",
        default="-",
        help="Text to send. Use '-' to read from stdin (default: -)"
    )
    send_parser.add_argument(
        "--no-bracketed-paste",
        action="store_true",
        help="Disable bracketed paste mode"
    )
    send_parser.add_argument(
        "--ipython",
        action="store_true",
        help="Force IPython mode (%cpaste for multiline code)"
    )
    send_parser.add_argument(
        "--python",
        action="store_true",
        help="Force standard Python mode (no %cpaste)"
    )

    # Connect command (placeholder for future implementation)
    subparsers.add_parser(
        "connect", help="Connect to a specific tmux pane (not implemented yet)"
    )

    return parser


def send_command(text: str, use_bracketed_paste: bool = True, force_ipython: bool = False, force_python: bool = False) -> int:
    """Execute the send command.

    Args:
        text: The text to send to the REPL.
        use_bracketed_paste: Whether to use bracketed paste mode.
        force_ipython: Force using IPython mode (%cpaste).
        force_python: Force using standard Python mode.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Find the target pane (the one to the right)
    target_pane = tmux.get_next_pane()

    if not target_pane:
        print("Error: No pane found to the right of the current pane", file=sys.stderr)
        return 1

    # Check if the target pane is running a Python REPL
    pane_command = tmux.get_pane_command(target_pane)
    if not python.is_python_repl(pane_command):
        print(f"Warning: The pane {target_pane} does not appear to be running a Python REPL",
              file=sys.stderr)
    
    # Send the text to the pane
    try:
        # Use the common interface that handles all cases
        tmux.send_text_to_pane(target_pane, text, use_bracketed_paste)
        return 0
    except Exception as e:
        print(f"Error sending text: {e}", file=sys.stderr)
        return 1


def connect_command() -> int:
    """Execute the connect command (placeholder).
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    print("Connect command is not implemented yet.")
    print("Currently, repot always sends to the pane to the right.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
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

        # Apply preprocessing here to handle indentation
        text = python.preprocess_code(text)

        return send_command(
            text,
            not args.no_bracketed_paste,
            force_ipython=args.ipython,
            force_python=args.python
        )
    elif args.command == "connect":
        return connect_command()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
