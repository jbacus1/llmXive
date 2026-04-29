"""
SQLite-based caching layer for the Climate-Smart Agriculture project.

This module provides a thread-safe, persistent caching mechanism using SQLite.
It supports TTL-based expiration, cache invalidation, and atomic operations.

Usage:
    cache = CacheManager()
    cache.set("key", value, ttl=3600)
    value = cache.get("key")

Thread Safety:
    Uses thread-local connections with a lock for write operations.
    Safe for concurrent access from multiple threads.
"""

import sqlite3
import json
import time
import threading
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime


class CacheManager:
    """SQLite-based cache manager with TTL support."""

    def __init__(self, db_path: str = "data/cache.db"):
        """
        Initialize the cache manager.

        Args:
            db_path: Path to the SQLite database file (relative to project root)
        """
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._ensure_db_exists()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            with self._lock:
                if not hasattr(self._local, 'connection') or self._local.connection is None:
                    # Ensure parent directory exists
                    self.db_path.parent.mkdir(parents=True, exist_ok=True)
                    self._local.connection = sqlite3.connect(
                        str(self.db_path),
                        check_same_thread=False,
                        timeout=30.0
                    )
                    self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _ensure_db_exists(self):
        """Create the cache table if it doesn't exist."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL,
                    created_at REAL
                )
            ''')
            # Create index for faster cleanup of expired entries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
            ''')
            conn.commit()

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key (string, must be unique)
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (None = never expires)

        Returns:
            True if successful, False if serialization failed
        """
        try:
            value_json = json.dumps(value, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value for key '{key}' is not JSON serializable: {e}")

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            expires_at = time.time() + ttl if ttl else None
            created_at = time.time()

            cursor.execute('''
                INSERT OR REPLACE INTO cache (key, value, expires_at, created_at)
                VALUES (?, ?, ?, ?)
            ''', (key, value_json, expires_at, created_at))

            conn.commit()
            return True

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT value, expires_at FROM cache WHERE key = ?
            ''', (key,))

            row = cursor.fetchone()

            if not row:
                return None

            # Check if expired
            if row['expires_at'] and time.time() > row['expires_at']:
                self.delete(key)
                return None

            try:
                return json.loads(row['value'])
            except json.JSONDecodeError:
                return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if it didn't exist
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
            conn.commit()

            return cursor.rowcount > 0

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries deleted
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache')
            conn.commit()
            return cursor.rowcount

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of expired entries deleted
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            current_time = time.time()
            cursor.execute('''
                DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?
            ''', (current_time,))

            conn.commit()
            return cursor.rowcount

    def get_all_keys(self) -> list:
        """
        Get all cache keys.

        Returns:
            List of all cache keys
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT key FROM cache')

            return [row['key'] for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) as count FROM cache')
            total = cursor.fetchone()['count']

            current_time = time.time()
            cursor.execute('''
                SELECT COUNT(*) as count FROM cache 
                WHERE expires_at IS NULL OR expires_at > ?
            ''', (current_time,))
            valid = cursor.fetchone()['count']

            return {
                'total_keys': total,
                'valid_keys': valid,
                'expired_keys': total - valid,
                'db_path': str(self.db_path)
            }

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache (and is not expired).

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired
        """
        return self.get(key) is not None

    def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> int:
        """
        Store multiple values in the cache.

        Args:
            items: Dictionary of key-value pairs to cache
            ttl: Time-to-live in seconds (None = never expires)

        Returns:
            Number of items successfully cached
        """
        count = 0
        for key, value in items.items():
            try:
                if self.set(key, value, ttl):
                    count += 1
            except ValueError:
                continue
        return count

    def get_many(self, keys: list) -> Dict[str, Any]:
        """
        Retrieve multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs for keys that exist and are not expired
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def close(self):
        """Close the database connection."""
        with self._lock:
            if hasattr(self._local, 'connection') and self._local.connection:
                self._local.connection.close()
                self._local.connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __del__(self):
        """Close database connection on cleanup."""
        self.close()


# Convenience function for single-instance cache
_default_cache: Optional[CacheManager] = None
_cache_lock = threading.Lock()

def get_cache() -> CacheManager:
    """Get the default cache instance (singleton pattern)."""
    global _default_cache
    with _cache_lock:
        if _default_cache is None:
            _default_cache = CacheManager()
        return _default_cache


# Module-level convenience functions for simple usage
def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set a value in the default cache."""
    return get_cache().set(key, value, ttl)


def cache_get(key: str) -> Optional[Any]:
    """Get a value from the default cache."""
    return get_cache().get(key)


def cache_delete(key: str) -> bool:
    """Delete a key from the default cache."""
    return get_cache().delete(key)


def cache_clear() -> int:
    """Clear the default cache."""
    return get_cache().clear()


def cache_cleanup() -> int:
    """Clean up expired entries from the default cache."""
    return get_cache().cleanup_expired()


def cache_exists(key: str) -> bool:
    """Check if a key exists in the default cache."""
    return get_cache().exists(key)