"""Template files for snackbox."""

from importlib import resources
from pathlib import Path


def get_template_path(name: str) -> Path:
    """Get the path to a template file."""
    return resources.files(__package__).joinpath(name)


def read_template(name: str) -> str:
    """Read a template file and return its contents."""
    return resources.files(__package__).joinpath(name).read_text()
