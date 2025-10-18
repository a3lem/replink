"""Zellij target implementation."""

import subprocess
from dataclasses import dataclass, field

from replink.targets.common import MetaK, SendOptions
from replink.logging import logger


@dataclass
class ZellijTarget:
    """Zellij target implementation.

    Zellij only supports relative directional positioning (no numeric pane IDs).
    Both bracketed paste and non-bracketed paste modes are supported.
    """

    pane_direction: str = field(
        default="current",
        metadata={
            MetaK.ALIASES: ["pane", "p"],
            MetaK.EXAMPLES: ["current", "right", "left", "up", "down"],
        },
    )
    session_id: str = field(
        default="current",
        metadata={
            MetaK.ALIASES: ["s", "session"],
            MetaK.EXAMPLES: ["current", "my-session"],
        },
    )

    def __post_init__(self):
        """Validate the zellij target configuration."""
        valid_directions = {"current", "right", "left", "up", "down"}
        if self.pane_direction not in valid_directions:
            directions_str = ", ".join(valid_directions)
            raise ValueError(
                f"Invalid pane_direction: {self.pane_direction}. "
                f"Must be one of: {directions_str}"
            )

    def send(self, text: str, opts: SendOptions) -> None:
        """Send text to a zellij pane.

        Supports both bracketed paste and non-bracketed paste modes.
        This follows vim-slime's implementation.

        Args:
            text: Text to send.
            opts: Send options.
        """
        if not text:
            return

        _send_to_zellij(
            session_id=self.session_id,
            pane_direction=self.pane_direction,
            text=text,
            use_bracketed_paste=opts.use_bracketed_paste,
        )


def _build_zellij_cmd(session_id: str) -> list[str]:
    """Build the base zellij command.

    Args:
        session_id: Session ID or "current" for the current session.

    Returns:
        Base zellij command as a list.
    """
    if session_id != "current":
        return ["zellij", "-s", session_id]
    return ["zellij"]


def _send_to_zellij(
    session_id: str, pane_direction: str, text: str, use_bracketed_paste: bool
) -> None:
    """Send text to a zellij pane.

    This follows vim-slime's approach:
    1. Move focus to target pane (if not current)
    2. For bracketed paste:
       - Strip trailing newline(s) from text
       - Send bracketed paste start sequence (ESC[200~)
       - Send text using write-chars
       - Send bracketed paste end sequence (ESC[201~)
       - Send newline if we stripped one (to execute the code)
    3. For non-bracketed paste:
       - Send text using write-chars (no escape sequences)
    4. Move focus back (if we moved)

    Args:
        session_id: Zellij session ID.
        pane_direction: Direction of target pane (current, right, left, up, down).
        text: Text to send.
        use_bracketed_paste: Whether to use bracketed paste mode.
    """
    base_cmd = _build_zellij_cmd(session_id)

    # Calculate opposite direction for focus restoration
    opposite_direction = {
        "right": "left",
        "left": "right",
        "up": "down",
        "down": "up",
        "current": "current",
    }

    # Move focus to target pane if needed
    if pane_direction != "current":
        logger.debug(f"Moving focus to {pane_direction} pane")
        _ = subprocess.run(
            [*base_cmd, "action", "move-focus", pane_direction],
            capture_output=True,
            check=True,
        )

    if use_bracketed_paste:
        # Strip trailing newlines (any of \r\n, \r, or \n)
        text_stripped = text.rstrip("\r\n")
        has_trailing_newline = len(text) != len(text_stripped)

        logger.debug(f"Bracketed paste mode: {has_trailing_newline=}")

        # Send bracketed paste start sequence: ESC[200~
        # Decimal codes: 27 91 50 48 48 126
        logger.debug("Sending bracketed paste start sequence")
        _ = subprocess.run(
            [*base_cmd, "action", "write", "27", "91", "50", "48", "48", "126"],
            capture_output=True,
            check=True,
        )

        # Send the text (without trailing newline)
        logger.debug(f"Sending text ({len(text_stripped)} chars)")
        _ = subprocess.run(
            [*base_cmd, "action", "write-chars", text_stripped],
            capture_output=True,
            check=True,
        )

        # Send bracketed paste end sequence: ESC[201~
        # Decimal codes: 27 91 50 48 49 126
        logger.debug("Sending bracketed paste end sequence")
        _ = subprocess.run(
            [*base_cmd, "action", "write", "27", "91", "50", "48", "49", "126"],
            capture_output=True,
            check=True,
        )

        # Send Enter key to execute the code
        # Python REPL needs TWO enters: one to end the paste, one to execute
        # Use carriage return (13) for Enter key
        # See: https://github.com/zellij-org/zellij/discussions/2228
        if has_trailing_newline:
            logger.debug("Sending first Enter key")
            _ = subprocess.run(
                [*base_cmd, "action", "write", "13"],
                capture_output=True,
                check=True,
            )
            logger.debug("Sending second Enter key to execute")
            _ = subprocess.run(
                [*base_cmd, "action", "write", "13"],
                capture_output=True,
                check=True,
            )
    else:
        # Non-bracketed paste: just send the text as-is
        logger.debug(f"Non-bracketed paste mode: sending text ({len(text)} chars)")
        _ = subprocess.run(
            [*base_cmd, "action", "write-chars", text],
            capture_output=True,
            check=True,
        )

    # Move focus back if we moved
    if pane_direction != "current":
        move_back_direction = opposite_direction[pane_direction]
        logger.debug(f"Moving focus back to {move_back_direction}")
        _ = subprocess.run(
            [*base_cmd, "action", "move-focus", move_back_direction],
            capture_output=True,
            check=True,
        )
