import datetime
import threading
import time
from typing import Optional


class _ConnectionManager:
    def __init__(self, min_interval_seconds: float):
        self._lock = threading.Lock()
        self._last_timestamp = datetime.datetime.min
        self._min_interval_seconds = min_interval_seconds

    def __enter__(self):
        with self._lock:
            delta_seconds = (datetime.datetime.now() - self._last_timestamp).total_seconds()
            if delta_seconds < self._min_interval_seconds:
                wait_time = self._min_interval_seconds - delta_seconds
                time.sleep(wait_time)

            self._last_timestamp = datetime.datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


_connection_manager: Optional[_ConnectionManager] = None
_connection_manager_lock = threading.Lock()


def get_connection_manager() -> _ConnectionManager:
    global _connection_manager

    if _connection_manager is None:
        with _connection_manager_lock:
            if _connection_manager is None:
                _connection_manager = _ConnectionManager(min_interval_seconds=0.2)

    return _connection_manager
