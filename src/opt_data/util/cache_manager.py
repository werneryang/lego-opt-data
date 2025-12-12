"""
Cache management utilities with compression and preloading support.

This module provides optimized cache operations using Pickle + Gzip compression,
which is 3-5x faster than JSON and produces 50-70% smaller files.
"""

import gzip
import json
import logging
import pickle
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Centralized cache management with compression and preloading."""

    def __init__(self, cache_root: Path):
        """
        Initialize cache manager.

        Args:
            cache_root: Root directory for cache storage
        """
        self.cache_root = Path(cache_root)
        self._memory_cache: Dict[str, List[Dict[str, Any]]] = {}

    def _cache_key(self, symbol: str, trade_date: date) -> str:
        """Generate cache key for a symbol and date."""
        return f"{symbol}_{trade_date.isoformat()}"

    def _get_path(self, symbol: str, trade_date: date, use_compression: bool = True) -> Path:
        """Get cache file path for a symbol and date."""
        key = trade_date.isoformat()
        base_path = self.cache_root / symbol / key

        if use_compression:
            return base_path.with_suffix(".pkl.gz")
        return base_path.with_suffix(".json")

    def save(
        self,
        symbol: str,
        trade_date: date,
        data: List[Dict[str, Any]],
        use_compression: bool = True,
    ) -> Path:
        """
        Save cache data with optional compression.

        Args:
            symbol: Symbol to cache
            trade_date: Trade date
            data: List of contract dictionaries to cache
            use_compression: If True, use Pickle+Gzip; if False, use JSON

        Returns:
            Path to saved cache file
        """
        cache_path = self._get_path(symbol, trade_date, use_compression)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if use_compression:
                with gzip.open(cache_path, "wb", compresslevel=6) as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            logger.debug(
                f"Saved cache for {symbol} {trade_date}: {len(data)} contracts "
                f"({cache_path.stat().st_size} bytes)"
            )

            # Update memory cache
            cache_key = self._cache_key(symbol, trade_date)
            self._memory_cache[cache_key] = data

            return cache_path

        except Exception as exc:
            logger.error(
                f"Failed to save cache for {symbol} {trade_date}: {exc}",
                exc_info=True,
            )
            raise

    def load(
        self,
        symbol: str,
        trade_date: date,
        use_memory_cache: bool = True,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Load cache data with automatic format detection.

        Attempts to load compressed format first, falls back to JSON if not found.

        Args:
            symbol: Symbol to load
            trade_date: Trade date
            use_memory_cache: If True, check memory cache first

        Returns:
            List of cached contracts, or None if not found
        """
        cache_key = self._cache_key(symbol, trade_date)

        # Check memory cache first
        if use_memory_cache and cache_key in self._memory_cache:
            logger.debug(f"Cache hit (memory) for {symbol} {trade_date}")
            return self._memory_cache[cache_key]

        # Try compressed format first
        compressed_path = self._get_path(symbol, trade_date, use_compression=True)
        if compressed_path.exists():
            try:
                with gzip.open(compressed_path, "rb") as f:
                    data = pickle.load(f)
                logger.debug(f"Cache hit (disk, compressed) for {symbol} {trade_date}")
                self._memory_cache[cache_key] = data
                return data
            except Exception as exc:
                logger.warning(f"Failed to load compressed cache for {symbol} {trade_date}: {exc}")

        # Fallback to JSON format
        json_path = self._get_path(symbol, trade_date, use_compression=False)
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                logger.debug(f"Cache hit (disk, JSON) for {symbol} {trade_date}")
                self._memory_cache[cache_key] = data
                return data
            except Exception as exc:
                logger.warning(f"Failed to load JSON cache for {symbol} {trade_date}: {exc}")

        logger.debug(f"Cache miss for {symbol} {trade_date}")
        return None

    def preload(self, symbols: List[str], trade_date: date) -> int:
        """
        Preload caches for multiple symbols into memory.

        Args:
            symbols: List of symbols to preload
            trade_date: Trade date

        Returns:
            Number of caches successfully preloaded
        """
        loaded = 0
        for symbol in symbols:
            cache_key = self._cache_key(symbol, trade_date)
            if cache_key not in self._memory_cache:
                data = self.load(symbol, trade_date, use_memory_cache=False)
                if data is not None:
                    loaded += 1

        logger.info(f"Preloaded {loaded}/{len(symbols)} caches for {trade_date}")
        return loaded

    def clear_memory_cache(self) -> None:
        """Clear the in-memory cache."""
        self._memory_cache.clear()
        logger.debug("Memory cache cleared")

    def migrate_to_compressed(self, symbol: str, trade_date: date) -> bool:
        """
        Migrate a JSON cache file to compressed format.

        Args:
            symbol: Symbol to migrate
            trade_date: Trade date

        Returns:
            True if migration successful, False otherwise
        """
        json_path = self._get_path(symbol, trade_date, use_compression=False)
        if not json_path.exists():
            return False

        try:
            # Load from JSON
            data = json.loads(json_path.read_text(encoding="utf-8"))

            # Save as compressed
            self.save(symbol, trade_date, data, use_compression=True)

            # Optionally delete old JSON file
            # json_path.unlink()  # Uncomment to delete after migration

            logger.info(f"Migrated cache for {symbol} {trade_date} to compressed format")
            return True

        except Exception as exc:
            logger.error(f"Failed to migrate cache for {symbol} {trade_date}: {exc}")
            return False


def migrate_all_caches(cache_root: Path, delete_old: bool = False) -> tuple[int, int]:
    """
    Migrate all JSON caches to compressed format.

    Args:
        cache_root: Root directory containing caches
        delete_old: If True, delete JSON files after successful migration

    Returns:
        Tuple of (successful_migrations, failed_migrations)
    """
    cache_manager = CacheManager(cache_root)
    success = 0
    failed = 0

    # Find all JSON cache files
    for json_path in cache_root.rglob("*.json"):
        if json_path.stem.startswith("."):
            continue

        try:
            # Extract symbol and date from path
            # Expected structure: cache_root/SYMBOL/YYYY-MM-DD.json
            symbol = json_path.parent.name
            date_str = json_path.stem
            trade_date = date.fromisoformat(date_str)

            if cache_manager.migrate_to_compressed(symbol, trade_date):
                success += 1
                if delete_old:
                    json_path.unlink()
            else:
                failed += 1

        except Exception as exc:
            logger.warning(f"Skipping {json_path}: {exc}")
            failed += 1

    logger.info(f"Migration complete: {success} successful, {failed} failed")
    return success, failed
