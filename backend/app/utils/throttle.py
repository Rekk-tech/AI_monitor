"""
Throttle Utility
Provides throttling for high-frequency event broadcasts.
"""

import time
import threading
from typing import Dict, Optional, Callable, Any
from functools import wraps


class Throttle:
    """
    Throttle class for limiting function call frequency.
    
    Usage:
        throttle = Throttle(interval_ms=100)
        
        # In a loop:
        if throttle.should_execute("audio_session_1"):
            broadcast_audio_metrics(...)
    """
    
    def __init__(self, interval_ms: int = 100):
        self.interval_ms = interval_ms
        self.interval_sec = interval_ms / 1000.0
        self._last_call: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def should_execute(self, key: str = "default") -> bool:
        """
        Check if enough time has passed since last execution.
        Returns True if should execute, False if should skip.
        """
        now = time.time()
        
        with self._lock:
            last = self._last_call.get(key, 0)
            if now - last >= self.interval_sec:
                self._last_call[key] = now
                return True
            return False
    
    def reset(self, key: str = "default"):
        """Reset throttle for a specific key"""
        with self._lock:
            if key in self._last_call:
                del self._last_call[key]
    
    def reset_all(self):
        """Reset all throttle keys"""
        with self._lock:
            self._last_call.clear()


# Pre-configured throttle instances for different use cases
# Audio: 100ms (10 Hz)
audio_throttle = Throttle(interval_ms=100)

# Video: 200ms (5 Hz)  
video_throttle = Throttle(interval_ms=200)

# Session state: 500ms (2 Hz)
session_throttle = Throttle(interval_ms=500)


def throttled(interval_ms: int = 100):
    """
    Decorator for throttling synchronous functions.
    
    Usage:
        @throttled(interval_ms=100)
        def my_frequent_function():
            ...
    """
    throttle = Throttle(interval_ms=interval_ms)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name + first arg (session_id) as key
            key = func.__name__
            if args:
                key = f"{func.__name__}_{args[0]}"
            
            if throttle.should_execute(key):
                return func(*args, **kwargs)
            return None
        return wrapper
    return decorator
