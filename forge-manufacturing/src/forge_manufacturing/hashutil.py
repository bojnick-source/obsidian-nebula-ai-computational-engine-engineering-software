"""SHA-256 hashing utilities for manufacturing artifacts.

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/sfcs_mdp/hashutil.py)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

_CHUNK_SIZE: int = 1024 * 1024  # 1 MiB — memory-efficient for large build artifacts


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 digest of *data*."""
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of the file at *path*.

    Reads in :data:`_CHUNK_SIZE` chunks to avoid loading large files into memory.

    Raises:
        OSError: If *path* cannot be opened for reading.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_files(paths: Iterable[Path], base_dir: Path) -> dict[str, str]:
    """Hash every regular file in *paths*, keyed by POSIX path relative to *base_dir*.

    Non-file entries (directories, symlinks to directories) are silently skipped.

    Returns:
        Mapping of ``relative/posix/path`` → hex SHA-256 digest.
    """
    hashes: dict[str, str] = {}
    for path in paths:
        if path.is_file():
            relative = path.relative_to(base_dir).as_posix()
            hashes[relative] = sha256_file(path)
    return hashes
