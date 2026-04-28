"""Cache manager for downloading and storing external dependencies."""

import os
import shutil
import zipfile
from collections.abc import Callable
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from snackbox.errors import CacheError


def get_cache_dir() -> Path:
    """Get the cache directory path.

    Uses SNACKBOX_CACHE_DIR env var if set, otherwise ~/.snackbox/cache/
    """
    env_dir = os.environ.get("SNACKBOX_CACHE_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".snackbox" / "cache"


class CacheManager:
    """Manages the download cache for snackbox dependencies."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or get_cache_dir()
        self.python_dir = self.cache_dir / "python"
        self.tools_dir = self.cache_dir / "tools"

    def ensure_dirs(self) -> None:
        """Create cache directories if they don't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.python_dir.mkdir(exist_ok=True)
        self.tools_dir.mkdir(exist_ok=True)

    def download(
        self,
        url: str,
        dest: Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        """Download a file from URL to destination.

        Args:
            url: URL to download from
            dest: Destination file path
            progress_callback: Optional callback(downloaded_bytes, total_bytes)

        Returns:
            Path to the downloaded file

        Raises:
            CacheError: If download fails
        """
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            request = Request(url, headers={"User-Agent": "snackbox"})
            with urlopen(request, timeout=30) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 8192

                with open(dest, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

        except HTTPError as e:
            raise CacheError(f"HTTP error downloading {url}: {e.code} {e.reason}") from e
        except URLError as e:
            raise CacheError(f"Failed to download {url}: {e.reason}") from e
        except OSError as e:
            raise CacheError(f"Failed to write {dest}: {e}") from e

        return dest

    def extract_zip(self, zip_path: Path, dest_dir: Path) -> Path:
        """Extract a zip file to destination directory.

        Args:
            zip_path: Path to the zip file
            dest_dir: Directory to extract to

        Returns:
            Path to the extraction directory

        Raises:
            CacheError: If extraction fails
        """
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(dest_dir)
        except zipfile.BadZipFile as e:
            raise CacheError(f"Invalid zip file {zip_path}: {e}") from e
        except OSError as e:
            raise CacheError(f"Failed to extract {zip_path}: {e}") from e

        return dest_dir

    def get_python_zip(self, version: str, arch: str = "amd64") -> Path:
        """Get path to cached Python embeddable zip.

        Args:
            version: Python version (e.g., "3.12.10")
            arch: Architecture ("amd64" or "win32")

        Returns:
            Path where the zip is/should be cached
        """
        filename = f"python-{version}-embed-{arch}.zip"
        return self.python_dir / filename

    def get_python_url(self, version: str, arch: str = "amd64") -> str:
        """Get download URL for Python embeddable zip."""
        return f"https://www.python.org/ftp/python/{version}/python-{version}-embed-{arch}.zip"

    def list_cached_items(self) -> dict[str, list[str]]:
        """List all cached items.

        Returns:
            Dict with categories as keys and lists of filenames as values
        """
        items: dict[str, list[str]] = {
            "python": [],
            "tools": [],
        }

        if self.python_dir.exists():
            items["python"] = sorted(f.name for f in self.python_dir.iterdir())

        if self.tools_dir.exists():
            items["tools"] = sorted(f.name for f in self.tools_dir.iterdir())

        return items

    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total = 0
        if self.cache_dir.exists():
            for f in self.cache_dir.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
        return total

    def clean(self) -> None:
        """Remove all cached files."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
