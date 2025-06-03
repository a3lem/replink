"""Command line interface for replink."""

import argparse
import sys
import typing as T
import logging

from replink.core import send
from replink.languages.common import Language
from replink.targets.common import (
    SendOptions,
    TargetType,
    parse_target_config_str,
    target_from_cfg_data,
)
from replink.logging import logger


def create_cli_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="replink",
        description="Send text to a REPL in tmux",
    )

    # Add global debug flag
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Send command
    send_parser = subparsers.add_parser(
        "send", help="Send text to a REPL running in a different pane"
    )
    send_parser.add_argument(
        "text",
        nargs="?",
        default="-",
        help="Code to send. Use '-' to read from stdin (default: -)",
    )

    # REPL type option
    send_parser.add_argument(
        "-l",
        "--lang",
        dest="language",
        choices=Language,
        required=True,
        help="Name of language to send (affects preprocessing)",
    )

    send_parser.add_argument(
        "-t",
        "--target",
        required=True,
        help="Target config, e.g. `tmux:p=1` ('use tmux, send to pane 1')",
    )

    # Additional options (mutually exclusive)
    mode_group = send_parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "-N",
        "--no-bpaste",
        action="store_true",
        help="Disable bracketed paste mode (required e.g. for builtin Python REPL < 3.13)",
    )
    mode_group.add_argument(
        "--ipy-cpaste",
        action="store_true",
        help="Special case. Use IPython's %%cpaste command (IPython only)",
    )
    #
    # Connect command (placeholder for future implementation)

    _ = subparsers.add_parser(
        "connect", help="Connect to a specific tmux pane (not implemented yet)"
    )
    #
    # Connect command (placeholder for future implementation)
    _ = subparsers.add_parser("debug-target", help="Debug target string (Not implemented yet)")

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
    language = args.language  # We only support Python for now
    match language:
        case Language.PYTHON:
            from replink.languages.python import PythonProcessor

            language = PythonProcessor(
                use_bracketed_paste=not args.no_bpaste, use_cpaste=args.ipy_cpaste
            )
        case _:
            raise ValueError(f"Unsupported language: {language}]")

    # breakpoint()
    target_name, target_cfg_data = parse_target_config_str(args.target)
    match target_name:
        case TargetType.TMUX:
            from replink.targets.tmux import TmuxTarget

            target = target_from_cfg_data(target_cfg_data, TmuxTarget)
        case _:
            raise ValueError(f"Unsupported target: {target_name}")

    # Check bracketed paste option
    send_opts = SendOptions(use_bracketed_paste=not args.no_bpaste)

    # Create target configuration
    try:
        # For now, we only support tmux
        send(text, target, language, send_opts)
        return 0
    except Exception as e:
        logger.debug(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def connect_command() -> int:
    """Execute the connect command (placeholder).

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger.debug("Connect command is not implemented yet.")
    return 0


def main(argv: T.Optional[list[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code.
    """
    parser = create_cli_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # Configure logging based on debug flag
    if args.debug:
        # Set up logging for replink logger only
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.debug("Debug logging enabled")

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
