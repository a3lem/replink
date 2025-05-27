"""Tmux target implementation."""

import subprocess
from dataclasses import dataclass
from typing import Optional

from repot.targets.interface import TargetConfig, TARGETS


@dataclass
class TmuxConfig(TargetConfig):
    """Configuration for tmux target."""
    pane_id: str
    use_bracketed_paste: bool = True


class TmuxTarget:
    """Tmux target implementation."""
    
    @staticmethod
    def config() -> TmuxConfig:
        """Configure the tmux target.
        
        Currently, this automatically gets the pane to the right of the current pane.
        In the future, this could be expanded to allow selecting any pane.
        
        Returns:
            TmuxConfig with the target pane ID.
        """
        target_pane = get_next_pane()
        if not target_pane:
            raise ValueError("No pane found to the right of the current pane")
        
        return TmuxConfig(pane_id=target_pane)
    
    @staticmethod
    def send(config: TmuxConfig, text: str) -> None:
        """Send text to a tmux pane.
        
        Args:
            config: Tmux configuration.
            text: Text to send.
        """
        if not text:
            return

        
        # Decide which method to use based on configuration and text length
        if config.use_bracketed_paste:
            if len(text) > 500:
                send_with_buffer(config.pane_id, text, bracketed_paste=True)
            else:
                send_with_bracketed_paste(config.pane_id, text)
        else:
            # For non-bracketed paste, send as a single block
            # The language escape function has already formatted the text properly
            if len(text) > 500:
                # Use chunking for long text even without bracketed paste
                send_with_buffer(config.pane_id, text, bracketed_paste=False)
            else:
                send_without_bracketed_paste(config.pane_id, text)


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


def _send_to_tmux(target_id: str, text: str, bracketed_paste: bool, chunk_size: Optional[int] = None) -> None:
    """Common implementation for sending text to tmux.
    
    This follows vim-slime's approach exactly:
    1. For bracketed paste: strip trailing newlines and track if we need to send Enter
    2. For non-bracketed paste: send text as-is (Python REPL handles newlines)
    3. Cancel any existing command
    4. Load text into buffer (optionally in chunks)
    5. Paste buffer with or without bracketed paste mode
    6. Send Enter if needed (only for bracketed paste mode)
    
    Args:
        target_id: The target tmux pane ID.
        text: The text to send.
        bracketed_paste: Whether to use bracketed paste mode (-p flag).
        chunk_size: If provided, send text in chunks of this size.
    """
    
    if bracketed_paste:
        # For bracketed paste, strip trailing newlines and send Enter separately
        text_to_paste = text.rstrip('\r\n')
        # Claude! This variable is assigned but never used, whereas vim-slime does use it.
        has_newline = len(text) != len(text_to_paste)
    else:
        # For non-bracketed paste (Python < 3.13), send text as-is
        # The Python escape function already handles proper formatting
        text_to_paste = text
        # Claude! This variable is assigned but never used, whereas vim-slime does use it.
        has_newline = False  # Don't send Enter separately
    
    
    if not text_to_paste:
        return
    
    # Cancel any existing command first (only need to do this once)
    subprocess.run(
        ["tmux", "send-keys", "-X", "-t", target_id, "cancel"],
        capture_output=True
    )
    
    # Determine paste command based on bracketed paste mode
    paste_cmd = ["tmux", "paste-buffer", "-d"]
    if bracketed_paste:
        paste_cmd.append("-p")
    paste_cmd.extend(["-t", target_id])
    
    if chunk_size:
        # Send text in chunks (vim-slime uses 1000 character chunks)
        for i in range(0, len(text_to_paste), chunk_size):
            chunk = text_to_paste[i:i + chunk_size]
            
            
            # Load chunk into buffer
            subprocess.run(
                ["tmux", "load-buffer", "-"],
                input=chunk,
                text=True,
                check=True
            )
            
            # Paste buffer
            subprocess.run(paste_cmd, check=True)
    else:
        # Send all text at once
        
        subprocess.run(
            ["tmux", "load-buffer", "-"],
            input=text_to_paste,
            text=True,
            check=True
        )
        
        # Paste buffer
        subprocess.run(paste_cmd, check=True)
    
    # Send Enter key to execute the code
    # Repot always sends Enter because its purpose is to send code for execution
    # This differs from vim-slime which only sends Enter if text had trailing newline
    subprocess.run(
        ["tmux", "send-keys", "-t", target_id, "Enter"],
        check=True
    )
    
    # For bracketed paste, send another Enter to execute code blocks
    # Python REPLs need a blank line after indented blocks
    if bracketed_paste:
        subprocess.run(
            ["tmux", "send-keys", "-t", target_id, "Enter"],
            check=True
        )


def send_with_bracketed_paste(target_id: str, text: str) -> None:
    """Send text using bracketed paste mode.
    
    This is the preferred method for REPLs that support it.
    Uses vim-slime's approach: load-buffer + paste-buffer with -p flag.
    
    Args:
        target_id: The target tmux pane ID.
        text: The text to send.
    """
    _send_to_tmux(target_id, text, bracketed_paste=True)


def send_with_buffer(target_id: str, text: str, bracketed_paste: bool = True) -> None:
    """Send text using tmux's load-buffer and paste-buffer commands.
    
    This method is used for longer texts. Follows vim-slime's chunking approach.
    
    Args:
        target_id: The ID of the target tmux pane.
        text: The text to send.
        bracketed_paste: Whether to use bracketed paste mode.
    """
    # vim-slime uses 1000 character chunks
    _send_to_tmux(target_id, text, bracketed_paste=bracketed_paste, chunk_size=1000)


def send_without_bracketed_paste(target_id: str, text: str) -> None:
    """Send text without using bracketed paste.
    
    This method is designed specifically for Python REPL < 3.13 which doesn't 
    support bracketed paste. Uses vim-slime's approach: paste-buffer without -p flag.
    
    Args:
        target_id: The target tmux pane ID.
        text: The text to send.
    """
    _send_to_tmux(target_id, text, bracketed_paste=False)


# Register the tmux target
TARGETS['tmux'] = TmuxTarget
