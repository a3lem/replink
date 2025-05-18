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


def send_to_repl(target_pane: str, text: str, repl_type: str, 
                use_bracketed_paste: bool = True, use_cpaste: bool = False,
                is_py13: bool = False) -> None:
    """Send text to the specified REPL type.
    
    Args:
        target_pane: The ID of the target tmux pane.
        text: The text to send.
        repl_type: Type of REPL: 'py', 'ipy', or 'ptpy'.
        use_bracketed_paste: Whether to use bracketed paste mode.
        use_cpaste: Whether to use IPython's %cpaste command.
        is_py13: Whether Python is version >= 3.13.
    """
    # Basic preprocessing for all REPL types
    text = python.preprocess_code(text)
    
    # For IPython with %cpaste
    if repl_type == 'ipy' and use_cpaste:
        send_with_cpaste(target_pane, text)
    
    # For Python < 3.13 without bracketed paste, use line-by-line mode
    elif repl_type == 'py' and not is_py13 and not use_bracketed_paste:
        send_line_by_line(target_pane, text)
    
    # For all REPLs that support bracketed paste
    elif use_bracketed_paste:
        # Python 3.13+, IPython, ptpython all support bracketed paste
        send_with_bracketed_paste(target_pane, text)
    
    # Fallback for any other case
    else:
        send_raw_keys(target_pane, text, False)


def send_line_by_line(target_pane: str, text: str) -> None:
    """Send Python code line by line to a REPL that doesn't support bracketed paste.
    
    This is primarily designed for Python < 3.13 REPL without bracketed paste.
    It handles indentation, empty lines, and multi-line expressions carefully.
    
    Args:
        target_pane: The tmux pane ID.
        text: The preprocessed Python code to send.
    """
    # Use the special line-by-line preprocessor for Python < 3.13
    commands = python.preprocess_for_line_mode(text)
    
    for cmd in commands:
        line = cmd['line']
        wait = cmd.get('wait_for_prompt', True)
        
        # Skip empty lines except when needed to execute a block
        if not line.strip() and not wait:
            continue
        
        # Send the line
        subprocess.run(
            ["tmux", "send-keys", "-t", target_pane, line],
            check=True
        )
        
        # Send Enter
        subprocess.run(
            ["tmux", "send-keys", "-t", target_pane, "Enter"],
            check=True
        )
        
        # Wait for the REPL to process the line and show a prompt
        # This is important for code that requires line-by-line execution
        if wait:
            time.sleep(0.15)  # Longer delay after statements that complete execution


def send_with_cpaste(target_pane: str, text: str) -> None:
    """Send Python code to IPython using the %cpaste command.
    
    This is the most reliable way to send complex multi-line code to IPython.
    
    Args:
        target_pane: The tmux pane ID.
        text: The Python code to send.
    """
    cpaste_steps = python.format_for_cpaste(text)
    
    for step in cpaste_steps:
        step_type = step.get('type')
        content = step.get('content')
        wait = step.get('wait_for_prompt', False)
        
        if step_type == 'delay':
            time.sleep(content)
        elif step_type == 'command':
            # Send the command
            subprocess.run(
                ["tmux", "send-keys", "-t", target_pane, content],
                check=True
            )
            # Send Enter
            subprocess.run(
                ["tmux", "send-keys", "-t", target_pane, "Enter"],
                check=True
            )
            # Wait if needed
            if wait:
                time.sleep(0.2)
        elif step_type == 'text':
            # Send the text directly
            subprocess.run(
                ["tmux", "send-keys", "-t", target_pane, content],
                check=True
            )


def send_with_bracketed_paste(target_pane: str, text: str) -> None:
    """Send text using bracketed paste mode.
    
    This is the preferred method for REPLs that support it (IPython,
    ptpython, Python 3.13+).
    
    Args:
        target_pane: The target tmux pane ID.
        text: The text to send.
    """
    # For large content, use buffer method
    if len(text) > 500:
        send_with_buffer(target_pane, text)
        return
    
    # Ensure exactly one trailing newline
    text = text.rstrip() + '\n'
    
    # Send the bracketed paste sequence
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, BRACKETED_PASTE_START],
        check=True
    )
    
    # Send the text content
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, text],
        check=True
    )
    
    # End bracketed paste
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, BRACKETED_PASTE_END],
        check=True
    )
    
    # Allow time for processing
    time.sleep(0.2)
    
    # Send Enter to execute
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, "Enter"],
        check=True
    )


def send_raw_keys(target_pane: str, text: str, use_bracketed_paste: bool = True) -> None:
    """Send raw text to the specified tmux pane with no special handling.
    
    Args:
        target_pane: The ID of the target tmux pane.
        text: The text to send.
        use_bracketed_paste: Whether to use bracketed paste mode.
    """
    if use_bracketed_paste:
        send_with_bracketed_paste(target_pane, text)
    else:
        # For multi-line text, line-by-line is more reliable
        if '\n' in text:
            for line in text.splitlines():
                if line.strip():  # Skip empty lines
                    subprocess.run(
                        ["tmux", "send-keys", "-t", target_pane, line],
                        check=True
                    )
                    subprocess.run(
                        ["tmux", "send-keys", "-t", target_pane, "Enter"],
                        check=True
                    )
                    time.sleep(0.05)
        else:
            # Single line can be sent directly
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
    # Make sure the text is properly formatted
    text = text.rstrip() + '\n'
        
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as temp:
        temp.write(text)
        temp.flush()
        
        # Load the buffer from the file
        subprocess.run(
            ["tmux", "load-buffer", temp.name],
            check=True
        )
    
    # Use bracketed paste mode with the buffer
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
    
    # Allow time for processing
    time.sleep(0.3)
    
    # Send Enter to execute
    subprocess.run(
        ["tmux", "send-keys", "-t", target_pane, "Enter"],
        check=True
    )
