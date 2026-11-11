"""Cache API skeleton. Complete TTL/LRU behavior without changing signatures."""


class TTLCache:
    def __init__(self, capacity, clock):
        self.capacity = capacity
        self.clock = clock
        self.entries = {}

    def set(self, key, value, ttl=None):
        self.entries[key] = value

    def get(self, key, default=None):
        return self.entries.get(key, default)

    def delete(self, key):
        if key not in self.entries:
            return False
        del self.entries[key]
        return True

    def __len__(self):
        return len(self.entries)
