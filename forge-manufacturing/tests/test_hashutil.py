"""Tests for forge_manufacturing.hashutil."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path


from forge_manufacturing.hashutil import hash_files, sha256_bytes, sha256_file


def test_sha256_bytes_known():
    """SHA-256 of empty bytes is the known digest."""
    empty_digest = hashlib.sha256(b"").hexdigest()
    assert sha256_bytes(b"") == empty_digest


def test_sha256_bytes_hello():
    data = b"hello"
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_bytes(data) == expected


def test_sha256_file_basic():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"forge test data")
        path = Path(f.name)
    try:
        expected = hashlib.sha256(b"forge test data").hexdigest()
        assert sha256_file(path) == expected
    finally:
        path.unlink(missing_ok=True)


def test_sha256_file_large(tmp_path: Path):
    """Files larger than 1 MiB chunk are hashed correctly."""
    big_file = tmp_path / "big.bin"
    data = b"X" * (2 * 1024 * 1024)  # 2 MiB
    big_file.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_file(big_file) == expected


def test_hash_files(tmp_path: Path):
    (tmp_path / "a.txt").write_bytes(b"aaa")
    (tmp_path / "b.txt").write_bytes(b"bbb")
    (tmp_path / "subdir").mkdir()  # directory — should be skipped

    result = hash_files(tmp_path.iterdir(), base_dir=tmp_path)
    assert "a.txt" in result
    assert "b.txt" in result
    assert "subdir" not in result
    assert result["a.txt"] == hashlib.sha256(b"aaa").hexdigest()


def test_hash_files_empty(tmp_path: Path):
    assert hash_files([], base_dir=tmp_path) == {}
