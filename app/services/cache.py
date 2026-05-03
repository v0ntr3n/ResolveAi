"""Caching utilities for improved performance."""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timedelta
from threading import Lock
from typing import Any


class LRUCache:
    """Thread-safe LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()
        self.lock = Lock()
    
    def _hash_key(self, key: str) -> str:
        """Create hash key for complex keys."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        hashed_key = self._hash_key(key)
        
        with self.lock:
            if hashed_key not in self.cache:
                return None
            
            value, timestamp = self.cache[hashed_key]
            
            # Check TTL
            if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
                del self.cache[hashed_key]
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(hashed_key)
            return value
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with timestamp."""
        hashed_key = self._hash_key(key)
        
        with self.lock:
            # Remove oldest if at capacity
            while len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            self.cache[hashed_key] = (value, datetime.now())
            self.cache.move_to_end(hashed_key)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        hashed_key = self._hash_key(key)
        
        with self.lock:
            if hashed_key in self.cache:
                del self.cache[hashed_key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
            }


class OrderCache:
    """Specialized cache for order data."""
    
    def __init__(self):
        self.cache = LRUCache(max_size=500, ttl_seconds=180)  # 3 minutes TTL
    
    def get_order(self, order_id: str) -> dict | None:
        """Get cached order data."""
        return self.cache.get(f"order:{order_id}")
    
    def set_order(self, order_id: str, order_data: dict) -> None:
        """Cache order data."""
        self.cache.set(f"order:{order_id}", order_data)
    
    def invalidate_order(self, order_id: str) -> None:
        """Invalidate cached order data."""
        self.cache.delete(f"order:{order_id}")
    
    def get_order_status(self, order_id: str) -> str | None:
        """Get cached order status."""
        return self.cache.get(f"status:{order_id}")
    
    def set_order_status(self, order_id: str, status: str) -> None:
        """Cache order status."""
        self.cache.set(f"status:{order_id}", status)


class PolicyCache:
    """Specialized cache for policy documents."""
    
    def __init__(self):
        self.cache = LRUCache(max_size=100, ttl_seconds=600)  # 10 minutes TTL
    
    def get_policy(self, query_hash: str) -> dict | None:
        """Get cached policy result."""
        return self.cache.get(f"policy:{query_hash}")
    
    def set_policy(self, query_hash: str, policy_data: dict) -> None:
        """Cache policy retrieval result."""
        self.cache.set(f"policy:{query_hash}", policy_data)
    
    def get_query_hash(self, query: str) -> str:
        """Generate hash for policy query."""
        return hashlib.md5(query.lower().encode()).hexdigest()


class MetricsCache:
    """Specialized cache for metrics/analytics data."""
    
    def __init__(self):
        self.cache = LRUCache(max_size=10, ttl_seconds=60)  # 1 minute TTL
    
    def get_metrics(self) -> dict | None:
        """Get cached metrics."""
        return self.cache.get("metrics:dashboard")
    
    def set_metrics(self, metrics: dict) -> None:
        """Cache metrics data."""
        self.cache.set("metrics:dashboard", metrics)
    
    def invalidate_metrics(self) -> None:
        """Invalidate cached metrics."""
        self.cache.delete("metrics:dashboard")


# Global cache instances
_order_cache: OrderCache | None = None
_policy_cache: PolicyCache | None = None
_metrics_cache: MetricsCache | None = None


def get_order_cache() -> OrderCache:
    """Get or create order cache instance."""
    global _order_cache
    if _order_cache is None:
        _order_cache = OrderCache()
    return _order_cache


def get_policy_cache() -> PolicyCache:
    """Get or create policy cache instance."""
    global _policy_cache
    if _policy_cache is None:
        _policy_cache = PolicyCache()
    return _policy_cache


def get_metrics_cache() -> MetricsCache:
    """Get or create metrics cache instance."""
    global _metrics_cache
    if _metrics_cache is None:
        _metrics_cache = MetricsCache()
    return _metrics_cache
