"""Target package for replink.

This package contains implementations of different targets that replink can send to.
Currently only tmux is supported.
"""

from replink.targets.interface import Target, TargetConfig, TARGETS