"""Build steps for snackbox."""

from snackbox.steps.assets import copy_assets
from snackbox.steps.deps import install_deps
from snackbox.steps.installer import build_installer
from snackbox.steps.launcher import build_launcher
from snackbox.steps.python import setup_python
from snackbox.steps.version import stamp_version
from snackbox.steps.wheel import build_wheel

__all__ = [
    "setup_python",
    "build_wheel",
    "install_deps",
    "build_launcher",
    "copy_assets",
    "stamp_version",
    "build_installer",
]
