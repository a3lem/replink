"""Target package for repot.

This package contains implementations of different targets that repot can send to.
Currently only tmux is supported.
"""

from repot.targets.interface import Target, TargetConfig, TARGETS