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
    
    # REPL type options (mutually exclusive)
    repl_group = send_parser.add_argument_group("REPL options")
    repl_type = repl_group.add_mutually_exclusive_group(required=True)
    repl_type.add_argument(
        "--py",
        action="store_true",
        help="Send to Python REPL (uses bracketed paste for Python >= 3.13)"
    )
    repl_type.add_argument(
        "--ipy",
        action="store_true",
        help="Send to IPython REPL (uses bracketed paste by default)"
    )
    repl_type.add_argument(
        "--ptpy",
        action="store_true",
        help="Send to ptpython REPL (uses bracketed paste)"
    )
    
    # Additional options
    repl_group.add_argument(
        "--no-bpaste",
        action="store_true",
        help="Disable bracketed paste mode (required for Python < 3.13)"
    )
    repl_group.add_argument(
        "--cpaste",
        action="store_true",
        help="Use IPython's %%cpaste command (only for --ipy)"
    )
    repl_group.add_argument(
        "--py13",
        action="store_true",
        help="Specify Python >= 3.13 (has built-in bracketed paste support)"
    )

    # Connect command (placeholder for future implementation)
    subparsers.add_parser(
        "connect", help="Connect to a specific tmux pane (not implemented yet)"
    )

    return parser


def send_command(text: str, repl_type: str, use_bracketed_paste: bool = True, 
                use_cpaste: bool = False, is_py13: bool = False) -> int:
    """Execute the send command.

    Args:
        text: The text to send to the REPL.
        repl_type: Type of REPL: 'py', 'ipy', or 'ptpy'.
        use_bracketed_paste: Whether to use bracketed paste mode.
        use_cpaste: Whether to use IPython's %cpaste command.
        is_py13: Whether Python is version >= 3.13.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Find the target pane (the one to the right)
    target_pane = tmux.get_next_pane()

    if not target_pane:
        print("Error: No pane found to the right of the current pane", file=sys.stderr)
        return 1
    
    # If cpaste is specified but not using IPython, show warning
    if use_cpaste and repl_type != 'ipy':
        print("Warning: --cpaste option is only valid with --ipy, ignoring", file=sys.stderr)
        use_cpaste = False
    
    # Process the code to handle indentation
    processed_text = python.preprocess_code(text)
    
    # Send the text to the pane
    try:
        # Send the text to the specified REPL type
        tmux.send_to_repl(
            target_pane,
            processed_text,
            repl_type=repl_type,
            use_bracketed_paste=use_bracketed_paste,
            use_cpaste=use_cpaste,
            is_py13=is_py13
        )
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

        # Determine REPL type
        repl_type = None
        if args.py:
            repl_type = 'py'
        elif args.ipy:
            repl_type = 'ipy'
        elif args.ptpy:
            repl_type = 'ptpy'
        
        # If no REPL type specified, show help
        if not repl_type:
            parser.print_help()
            print("\nError: You must specify a REPL type (--py, --ipy, or --ptpy)", 
                  file=sys.stderr)
            return 1

        return send_command(
            text,
            repl_type,
            use_bracketed_paste=not args.no_bpaste,
            use_cpaste=getattr(args, 'cpaste', False),
            is_py13=getattr(args, 'py13', False)
        )
    elif args.command == "connect":
        return connect_command()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())