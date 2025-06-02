"""Target interface for replink.

This module defines the interface that all target implementations must follow.
A target is a destination where code will be sent (e.g., tmux pane, screen window).
"""

import enum
from dataclasses import dataclass, fields as get_dataclass_fields, is_dataclass
from typing import Protocol, runtime_checkable

from replink.types import DataclassProtocol


class MetaK(enum.Enum):
    ALIASES = enum.auto()
    EXAMPLES = enum.auto()


@dataclass(frozen=True)
class SendOptions:
    use_bracketed_paste: bool = True


@runtime_checkable
class Target_P(DataclassProtocol, Protocol):
    """Protocol for all targets (must be dataclass)."""

    def send(self, text: str, opts: SendOptions) -> None:
        """Send text to the target.

        Args:
            text: Text to send to the target.
        """
        ...

@enum.unique
class TargetType(enum.StrEnum):
    TMUX = enum.auto()  # becomes 'tmux'


class TargetStringParseError(Exception): ...


class TargetConfigValidationError(Exception): ...


def parse_target_config_str(
    target_config_string: str,
) -> tuple[TargetType, dict[str, str]]:
    """
    Parse a target config string into a dataclass instance.

    Example:
        >>> parse_target_config_str('tmux:p=2')
        (<TargetType.TMUX: 'tmux'>, {'p': '2'})
    """

    if ":" not in target_config_string:
        raise TargetStringParseError(
            "Colon ':' missing, likely indicating missing target name, e.g. `tmux:`"
        )

    pieces = target_config_string.split(":")
    if len(pieces) != 2:
        raise TargetStringParseError("Expected exactly 1 colon ':'. Received multiple.")

    target_name, params_string = pieces

    try:
        target_type = TargetType(target_name.lower())
    except KeyError:
        raise TargetStringParseError(f"Unrecognized target name: {target_name}")

    cfg_data = {}
    for kv in params_string.split(","):
        if "=" not in kv:
            raise TargetStringParseError(f"Invalid parameter format: {kv}")
        k, v = kv.split("=")
        cfg_data[k] = v

    return target_type, cfg_data


def target_from_cfg_data(cfg_data: dict[str, str], target_cls: type[Target_P]) -> Target_P:
    """
    Example:
        >>> from replink.targets.tmux import TmuxTarget
        >>> target_from_cfg_data({"p": '2'}, TmuxTarget)
        TmuxTarget(pane_id=2)
    """
    assert is_dataclass(target_cls)
    cls_fields = get_dataclass_fields(target_cls)
    cfg_data = dict(cfg_data)
    kwargs = {}
    for field in cls_fields:
        get_k = None
        if field.name in cfg_data:
            get_k = field.name
        elif MetaK.ALIASES in field.metadata:
            for alias in field.metadata[MetaK.ALIASES]:
                if alias in cfg_data:
                    get_k = alias
        if get_k is None:
            continue
        val = cfg_data.pop(get_k)
        val = field.type(val)  # type: ignore
        kwargs[field.name] = val
    if cfg_data:
        raise TargetConfigValidationError(
            f"Received unexpected parameters for target config {target_cls}: {cfg_data}"
        )
    return target_cls(**kwargs)
