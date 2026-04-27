"""Tests for cache management."""

import os
from pathlib import Path
from unittest.mock import patch

from snackbox.cache import CacheManager, get_cache_dir
from snackbox.cache.manager import format_size


class TestGetCacheDir:
    def test_default_cache_dir(self):
        # Ensure SNACKBOX_CACHE_DIR is not set
        env = os.environ.copy()
        env.pop("SNACKBOX_CACHE_DIR", None)
        with patch.dict(os.environ, env, clear=True):
            cache_dir = get_cache_dir()
            assert cache_dir == Path.home() / ".snackbox" / "cache"

    def test_custom_cache_dir(self):
        with patch.dict(os.environ, {"SNACKBOX_CACHE_DIR": "/custom/cache"}):
            cache_dir = get_cache_dir()
            assert cache_dir == Path("/custom/cache")


class TestCacheManager:
    def test_init_default(self):
        cache = CacheManager()
        assert cache.cache_dir == get_cache_dir()

    def test_init_custom_dir(self, tmp_cache: Path):
        cache = CacheManager(cache_dir=tmp_cache)
        assert cache.cache_dir == tmp_cache

    def test_ensure_dirs(self, tmp_cache: Path):
        cache = CacheManager(cache_dir=tmp_cache)
        cache.ensure_dirs()
        assert cache.python_dir.exists()
        assert cache.tools_dir.exists()

    def test_get_python_zip_path(self, tmp_cache: Path):
        cache = CacheManager(cache_dir=tmp_cache)
        path = cache.get_python_zip("3.12.10", "amd64")
        assert path == tmp_cache / "python" / "python-3.12.10-embed-amd64.zip"

    def test_get_python_url(self, tmp_cache: Path):
        cache = CacheManager(cache_dir=tmp_cache)
        url = cache.get_python_url("3.12.10", "amd64")
        assert url == "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"

    def test_list_cached_items_empty(self, tmp_cache: Path):
        cache = CacheManager(cache_dir=tmp_cache)
        cache.ensure_dirs()
        items = cache.list_cached_items()
        assert items["python"] == []
        assert items["tools"] == []

    def test_list_cached_items_with_files(self, tmp_cache: Path):
        cache = CacheManager(cache_dir=tmp_cache)
        cache.ensure_dirs()

        # Create some test files
        (cache.python_dir / "python-3.12.10.zip").write_text("test")
        (cache.tools_dir / "get-pip.py").write_text("test")

        items = cache.list_cached_items()
        assert "python-3.12.10.zip" in items["python"]
        assert "get-pip.py" in items["tools"]

    def test_get_cache_size(self, tmp_cache: Path):
        cache = CacheManager(cache_dir=tmp_cache)
        cache.ensure_dirs()

        # Create a file with known size
        test_file = cache.python_dir / "test.txt"
        test_file.write_text("x" * 100)

        size = cache.get_cache_size()
        assert size >= 100

    def test_clean(self, tmp_cache: Path):
        cache = CacheManager(cache_dir=tmp_cache)
        cache.ensure_dirs()

        # Create some files
        (cache.python_dir / "test.zip").write_text("test")

        cache.clean()
        assert not tmp_cache.exists()

    def test_extract_zip(self, tmp_cache: Path, tmp_path: Path):
        import zipfile

        cache = CacheManager(cache_dir=tmp_cache)

        # Create a test zip file
        zip_path = tmp_path / "test.zip"
        extract_dir = tmp_path / "extracted"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("subdir/file2.txt", "content2")

        cache.extract_zip(zip_path, extract_dir)

        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "subdir" / "file2.txt").exists()


class TestFormatSize:
    def test_bytes(self):
        assert format_size(100) == "100.0 B"

    def test_kilobytes(self):
        assert format_size(1024) == "1.0 KB"
        assert format_size(2048) == "2.0 KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(1024 * 1024 * 5) == "5.0 MB"

    def test_gigabytes(self):
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"
