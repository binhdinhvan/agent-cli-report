from collections import OrderedDict

class TTLCache:
    def __init__(self, capacity, clock):
        self.capacity = capacity
        self.clock = clock
        self.entries = OrderedDict()

    def _purge(self):
        now = self.clock()
        for key, (_, deadline) in list(self.entries.items()):
            if deadline is not None and now > deadline:
                del self.entries[key]

    def set(self, key, value, ttl=None):
        self._purge()
        self.entries.pop(key, None)
        if ttl is not None and ttl <= 0:
            return None
        deadline = None if ttl is None else self.clock() + ttl
        self.entries[key] = (value, deadline)
        while len(self.entries) > self.capacity:
            self.entries.popitem(last=False)
        return None

    def get(self, key, default=None):
        self._purge()
        if key not in self.entries:
            return default
        self.entries.move_to_end(key)
        return self.entries[key][0]

    def delete(self, key):
        self._purge()
        if key not in self.entries:
            return False
        del self.entries[key]
        return True

    def __len__(self):
        self._purge()
        return len(self.entries)
