"""Tmux interaction module."""

import subprocess
import time
import tempfile
from typing import Optional, Dict, Any, List

from repot.repls import python

# Bracketed paste mode control sequences
BRACKETED_PASTE_START = "\033[200~"  # ESC [ 200 ~
BRACKETED_PASTE_END = "\033[201~"    # ESC [ 201 ~


def get_current_pane() -> str:
    """Get the ID of the current tmux pane."""
    result = subprocess.run(
        ["tmux", "display-message", "-p", "#{pane_id}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_next_pane() -> Optional[str]:
    """Get the ID of the pane to the right of the current pane."""
    current = get_current_pane()
    result = subprocess.run(
        ["tmux", "select-pane", "-R"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        return None
    
    target = get_current_pane()
    
    # Return to the original pane
    subprocess.run(["tmux", "select-pane", "-t", current], check=True)
    
    return target if target != current else None


def get_pane_content(pane_id: str) -> str:
    """Get the content of a tmux pane.
    
    Args:
        pane_id: The ID of the pane to get content from.
        
    Returns:
        The content of the pane as a string.
    """
    result = subprocess.run(
        ["tmux", "capture-pane", "-p", "-t", pane_id],
        capture_output=True,
        text=True,
    )
    return result.stdout


def get_pane_command(pane_id: str) -> str:
    """Get the command running in a tmux pane.
    
    Args:
        pane_id: The ID of the pane to check.
        
    Returns:
        The command name as a string.
    """
    result = subprocess.run(
        ["tmux", "display-message", "-p", "-t", pane_id, "#{pane_current_command}"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def extract_python_version(command: str) -> Optional[float]:
    """Extract Python version from a command string.
    
    Args:
        command: The command string, potentially containing version information.
        
    Returns:
        The Python version as a float (e.g., 3.12), or None if not found.
    """
    import re
    
    # Match patterns like 'python3.12', 'python3', 'python2.7', etc.
    version_match = re.search(r'python(?:[\d.]*(?P<major>\d+)\.(?P<minor>\d+)|(?P<major_only>\d+))', command.lower())
    
    if version_match:
        groups = version_match.groupdict()
        if groups['major'] is not None and groups['minor'] is not None:
            # We found both major and minor versions (e.g. python3.12)
            return float(f"{groups['major']}.{groups['minor']}")
        elif groups['major_only'] is not None:
            # We found only major version (e.g. python3)
            # Assume a ".0" minor version
            return float(f"{groups['major_only']}.0")
            
    return None


def send_text_to_pane(target_pane: str, text: str, use_bracketed_paste: bool = True) -> None:
    """Send text to the specified tmux pane.
    
    Args:
        target_pane: The ID of the target tmux pane.
        text: The text to send.
        use_bracketed_paste: Whether to use bracketed paste mode.
    """
    # Get information about the pane for REPL detection
    pane_command = get_pane_command(target_pane)
    pane_content = get_pane_content(target_pane)
    
    # Check if the target pane is a Python REPL
    if python.is_python_repl(pane_command):
        is_ipython = python.is_ipython_repl(pane_content)
        
        # Extract Python version from the command name
        python_version = extract_python_version(pane_command)
        
        # Process the code to handle indentation
        processed_text = python.preprocess_code(text)
        
        # IPython and Python 3.13+ handle indentation well with bracketed paste
        if is_ipython or (python_version is not None and python_version >= 3.13):
            send_with_bracketed_paste(target_pane, processed_text)
        # For older Python, need special handling for multi-line code
        else:
            if "\n" in processed_text:
                send_python_code(target_pane, processed_text)
            else:
                # Single line can be sent directly
                subprocess.run(
                    ["tmux", "send-keys", "-t", target_pane, processed_text, "Enter"],
                    check=True
                )
    else:
        # Generic text sending (could be extended for other REPL types)
        send_raw_keys(target_pane, text, use_bracketed_paste)




def send_with_bracketed_paste(target_pane: str, text: str) -> None:
    """Send text using bracketed paste mode.
    
    Bracketed paste mode tells the receiving program that the pasted text should
    be treated as a single unit, preserving things like indentation.
    
    Args:
        target_pane: The target tmux pane ID.
        text: The text to send.
    """
    if len(text) > 500:
        # For very large content, use the buffer method which is more reliable
        send_with_buffer(target_pane, text)
        return
    
    # Ensure text ends with a newline
    if not text.endswith("\n"):
        text = text + "\n"
    
    # Use send-keys with bracketed paste sequences
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, 
         f"{BRACKETED_PASTE_START}{text}{BRACKETED_PASTE_END}"],
        check=True
    )
    
    # Send Enter to execute
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, "Enter"],
        check=True
    )


def send_python_code(target_pane: str, text: str) -> None:
    """Send Python code to a standard Python REPL (< 3.13) maintaining indentation.
    
    This function handles Python's significant whitespace by ensuring proper
    indentation is maintained when sending multi-line code.
    
    Args:
        target_pane: The target tmux pane ID.
        text: The Python code to send.
    """
    # Split into lines and track indentation state
    lines = text.splitlines()
    
    # Keep track of indentation state to add extra newlines when needed
    indent_open = False
    
    for i, line in enumerate(lines):
        # Skip completely empty lines
        if not line.strip():
            continue
            
        # Check if this line is indented
        if line.startswith(" ") or line.startswith("\t"):
            indent_open = True
            
        # Send the current line
        subprocess.run(
            ["tmux", "send-keys", "-t", target_pane, line],
            check=True
        )
        
        # Send Enter
        subprocess.run(
            ["tmux", "send-keys", "-t", target_pane, "Enter"],
            check=True
        )
        
        # If we're ending an indented block, add an extra newline
        if indent_open and i < len(lines) - 1:
            next_line = lines[i + 1]
            if next_line.strip() and not next_line.startswith(" ") and not next_line.startswith("\t"):
                # Check if the next line is an "except", "else", "elif", or "finally" clause
                if not any(next_line.lstrip().startswith(kw) for kw in ["except", "else", "elif", "finally", "#"]):
                    indent_open = False
                    # Add extra newline to close the indented block
                    subprocess.run(
                        ["tmux", "send-keys", "-t", target_pane, "Enter"],
                        check=True
                    )
        
        # Small delay to let the REPL process the line
        time.sleep(0.05)
    
    # If the last line is indented, add an extra newline to execute the block
    if indent_open:
        subprocess.run(
            ["tmux", "send-keys", "-t", target_pane, "Enter"],
            check=True
        )


def execute_command_sequence(target_pane: str, commands: List[Dict[str, Any]]) -> None:
    """Execute a sequence of commands on a tmux pane.
    
    Args:
        target_pane: The ID of the target tmux pane.
        commands: List of command dictionaries with 'type' and 'content' keys.
    """
    for cmd in commands:
        cmd_type = cmd['type']
        content = cmd['content']
        
        if cmd_type == 'delay':
            time.sleep(content)
        elif cmd_type == 'text':
            subprocess.run(
                ["tmux", "send-keys", "-t", target_pane, content],
                check=True
            )
        elif cmd_type == 'keys':
            subprocess.run(
                ["tmux", "send-keys", "-t", target_pane, content],
                check=True
            )
        # 'bracketed_paste' type has been replaced by 'raw' type
        elif cmd_type == 'raw':
            # Send raw text without any processing
            subprocess.run(
                ["tmux", "send-keys", "-t", target_pane, content],
                check=True
            )
        elif cmd_type == 'buffer':
            send_with_buffer(target_pane, content)


def send_raw_keys(target_pane: str, text: str, use_bracketed_paste: bool = True) -> None:
    """Send raw text to the specified tmux pane with no special handling.
    
    Args:
        target_pane: The ID of the target tmux pane.
        text: The text to send.
        use_bracketed_paste: Whether to use bracketed paste mode.
    """
    # For large chunks of text, use load-buffer method
    if len(text) > 500:
        send_with_buffer(target_pane, text)
        return
        
    if use_bracketed_paste:
        # Use bracketed paste for any text
        send_with_bracketed_paste(target_pane, text)
    else:
        # Send directly without bracketed paste
        subprocess.run(
            ["tmux", "send-keys", "-t", target_pane, text, "Enter"],
            check=True
        )


def send_with_buffer(target_pane: str, text: str) -> None:
    """Send text using tmux's load-buffer and paste-buffer commands.
    
    This method is better for longer texts or texts with special characters.
    
    Args:
        target_pane: The ID of the target tmux pane.
        text: The text to send.
    """
    # Ensure text ends with a newline
    if not text.endswith("\n"):
        text = text + "\n"
        
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as temp:
        temp.write(text)
        temp.flush()
        
        # Load the buffer from the file
        subprocess.run(
            ["tmux", "load-buffer", temp.name],
            check=True
        )
    
    # Use bracketed paste mode with the buffer to preserve formatting
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, BRACKETED_PASTE_START],
        check=True
    )
    
    # Paste the buffer
    subprocess.run(
        ["tmux", "paste-buffer", "-t", target_pane],
        check=True
    )
    
    # End bracketed paste mode
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, BRACKETED_PASTE_END],
        check=True
    )
    
    # Small delay to ensure the text is fully processed
    time.sleep(0.1)
    
    # Send Enter to execute
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, "Enter"],
        check=True
    )


