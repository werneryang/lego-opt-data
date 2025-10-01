"""Tools for registering and resolving option market data sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable


@dataclass
class DataCatalog:
    """Simple registry that maps dataset keys to file system locations.

    Parameters
    ----------
    root:
        Base directory that holds all dataset files. The registry stores
        paths relative to this root so the project remains portable.
    sources:
        Optional initial mapping of dataset keys to relative paths. Each
        path is resolved against the root directory on access.
    """

    root: Path
    sources: Dict[str, Path] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()
        for key, path in list(self.sources.items()):
            self.sources[key] = self._ensure_within_root(key, path)

    def register(self, name: str, relative_path: Path | str) -> Path:
        """Register a dataset by storing its path relative to the root."""

        resolved = self._ensure_within_root(name, Path(relative_path))
        self.sources[name] = resolved
        return resolved

    def register_many(self, items: Iterable[tuple[str, Path | str]]) -> None:
        """Register multiple dataset entries at once."""

        for name, path in items:
            self.register(name, path)

    def resolve(self, name: str) -> Path:
        """Return the absolute path to the dataset for ``name``."""

        if name not in self.sources:
            available = ", ".join(sorted(self.sources)) or "<empty>"
            raise KeyError(f"No dataset registered under '{name}'. Known datasets: {available}")
        return self.sources[name]

    def _ensure_within_root(self, name: str, relative_path: Path) -> Path:
        """Resolve *relative_path* against the root and ensure it is local."""

        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(
                f"Dataset '{name}' resolves outside of the project root: {candidate}"
            ) from exc
        return candidate
