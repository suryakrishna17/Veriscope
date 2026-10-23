"""Private file storage behind an interface. Keys are opaque; paths never leave the server."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

_KEY = re.compile(r"^[a-z0-9][a-z0-9/_.-]{0,250}$")


class StorageBackend(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...


class LocalStorage(StorageBackend):
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not _KEY.match(key) or ".." in key:
            raise ValueError("invalid storage key")
        p = (self.root / key).resolve()
        if self.root not in p.parents:
            raise ValueError("storage key escapes root")
        return p

    def put(self, key: str, data: bytes) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".part")
        tmp.write_bytes(data)
        tmp.replace(p)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()
