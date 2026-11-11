"""An instance-local cache with TTL expiration and LRU eviction."""

from collections import OrderedDict


class TTLCache:
    def __init__(self, capacity, clock):
        self.capacity = capacity
        self.clock = clock
        # Entries are ordered from least to most recently used.
        self.entries = OrderedDict()

    def _purge_expired(self, now):
        expired = [
            key for key, (_, deadline) in self.entries.items()
            if deadline is not None and now >= deadline
        ]
        for key in expired:
            del self.entries[key]

    def set(self, key, value, ttl=None):
        now = self.clock()
        self._purge_expired(now)
        if ttl is not None and ttl <= 0:
            self.entries.pop(key, None)
            return

        deadline = None if ttl is None else now + ttl
        self.entries[key] = (value, deadline)
        self.entries.move_to_end(key)
        while len(self.entries) > self.capacity:
            self.entries.popitem(last=False)

    def get(self, key, default=None):
        if key not in self.entries:
            return default
        value, deadline = self.entries[key]
        if deadline is not None and self.clock() >= deadline:
            del self.entries[key]
            return default
        self.entries.move_to_end(key)
        return value

    def delete(self, key):
        if key not in self.entries:
            return False
        _, deadline = self.entries.pop(key)
        return deadline is None or self.clock() < deadline

    def __len__(self):
        self._purge_expired(self.clock())
        return len(self.entries)
