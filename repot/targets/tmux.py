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

        _send_to_tmux(config.pane_id, text, bracketed_paste=config.use_bracketed_paste)


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


def _send_to_tmux(target_id: str, text: str, bracketed_paste: bool) -> None:
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
    # if bracketed_paste:
    #     # For bracketed paste, strip trailing newlines and track if we need Enter
    #     text_to_paste = text.rstrip('\r\n')
    #     has_newline = len(text) != len(text_to_paste)
    # else:
    #     # For non-bracketed paste, send text as-is (already processed by language)
    #     text_to_paste = text
    #     has_newline = False  # Don't send Enter separately

    text_to_paste = text
    print(f"{text_to_paste=}")
    
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
    
    chunk_size = 1000  # borrow vim-slime hardcoded value
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

    
    # Send Enter key to execute the code
    # For bracketed paste: always send exactly one Enter
    # (Python preprocessing ensures code ends with exactly one newline)
    # For non-bracketed paste: Enter is already included in the text
    if bracketed_paste:
        subprocess.run(
            ["tmux", "send-keys", "-t", target_id, "Enter"],
            check=True
        )


# Register the tmux target
TARGETS['tmux'] = TmuxTarget
