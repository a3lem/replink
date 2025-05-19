"""Tmux interaction module."""

import subprocess
import time
import tempfile
from typing import Optional, Dict, Any, List

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


def send_to_repl(target_id: str, steps: List[Dict[str, Any]]) -> None:
    """Send code to a REPL in a tmux pane.
    
    Args:
        target_id: The ID of the target tmux pane.
        steps: The steps to execute to send the code.
    """
    for step in steps:
        step_type = step.get('type')
        content = step.get('content')
        
        if step_type == 'delay':
            time.sleep(content)
        elif step_type == 'command':
            # Send the command
            subprocess.run(
                ["tmux", "send-keys", "-t", target_id, content],
                check=True
            )
            # Send Enter
            subprocess.run(
                ["tmux", "send-keys", "-t", target_id, "Enter"],
                check=True
            )
            # Wait if requested
            if step.get('wait_for_prompt', True):
                time.sleep(0.15)
        elif step_type == 'text':
            # Send the text directly
            subprocess.run(
                ["tmux", "send-keys", "-t", target_id, content],
                check=True
            )
            # Wait if requested
            if step.get('wait_for_prompt', False):
                time.sleep(0.15)
        elif step_type == 'keypress':
            # Send a single key
            subprocess.run(
                ["tmux", "send-keys", "-t", target_id, content],
                check=True
            )
        elif step_type == 'bracketed_paste':
            send_with_bracketed_paste(target_id, content)


def send_with_bracketed_paste(target_id: str, text: str) -> None:
    """Send text using bracketed paste mode.
    
    This is the preferred method for REPLs that support it.
    
    Args:
        target_id: The target tmux pane ID.
        text: The text to send.
    """
    # For large content, use buffer method
    if len(text) > 500:
        send_with_buffer(target_id, text)
        return
    
    # Ensure exactly one trailing newline
    text = text.rstrip() + '\n'
    
    # Send the bracketed paste sequence
    subprocess.run(
        ["tmux", "send-keys", "-t", target_id, BRACKETED_PASTE_START],
        check=True
    )
    
    # Send the text content
    subprocess.run(
        ["tmux", "send-keys", "-t", target_id, text],
        check=True
    )
    
    # End bracketed paste
    subprocess.run(
        ["tmux", "send-keys", "-t", target_id, BRACKETED_PASTE_END],
        check=True
    )
    
    # Allow time for processing
    time.sleep(0.2)
    
    # Send Enter to execute
    subprocess.run(
        ["tmux", "send-keys", "-t", target_id, "Enter"],
        check=True
    )


def send_with_buffer(target_id: str, text: str) -> None:
    """Send text using tmux's load-buffer and paste-buffer commands.
    
    This method is better for longer texts or texts with special characters.
    
    Args:
        target_id: The ID of the target tmux pane.
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
        ["tmux", "send-keys", "-t", target_id, BRACKETED_PASTE_START],
        check=True
    )
    
    # Paste the buffer
    subprocess.run(
        ["tmux", "paste-buffer", "-t", target_id],
        check=True
    )
    
    # End bracketed paste mode
    subprocess.run(
        ["tmux", "send-keys", "-t", target_id, BRACKETED_PASTE_END],
        check=True
    )
    
    # Allow time for processing
    time.sleep(0.3)
    
    # Send Enter to execute
    subprocess.run(
        ["tmux", "send-keys", "-t", target_id, "Enter"],
        check=True
    )