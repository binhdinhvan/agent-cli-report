import random
import unittest
from cache import TTLCache


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.cache = TTLCache(2, self.clock)

    def test_expiry_boundary(self):
        self.cache.set("a", 1, 2)
        self.clock.now = 1.999
        self.assertEqual(self.cache.get("a"), 1)
        self.clock.now = 2
        self.assertEqual(self.cache.get("a", "expired"), "expired")
        self.assertFalse(self.cache.delete("a"))
        self.assertEqual(len(self.cache), 0)

    def test_lru_hit_and_overwrite(self):
        for k in ("a", "b"):
            self.cache.set(k, k)
        self.cache.get("a")
        self.cache.set("c", "c")
        self.assertIsNone(self.cache.get("b"))
        self.cache.set("a", "new")
        self.cache.set("d", "d")
        self.assertIsNone(self.cache.get("c"))
        self.assertEqual(self.cache.get("a"), "new")
        self.assertEqual(len(self.cache), 2)

    def test_len_miss_do_not_refresh(self):
        self.cache.set("a", 1)
        self.cache.set("b", 2)
        self.assertEqual(len(self.cache), 2)
        self.cache.get("miss")
        self.cache.set("c", 3)
        self.assertIsNone(self.cache.get("a"))

    def test_expired_purged_before_eviction(self):
        self.cache.set("a", 1)
        self.cache.set("b", 2, 1)
        self.clock.now = 1
        self.cache.set("c", 3)
        self.assertEqual(self.cache.get("a"), 1)
        self.assertEqual(len(self.cache), 2)
        self.cache.set("c", 4, 1)
        self.clock.now = 2
        self.assertEqual(len(self.cache), 1)

    def test_deadline_replaced_and_zero_ttl(self):
        self.cache.set("a", 1, 1)
        self.cache.set("a", 2, 5)
        self.clock.now = 1
        self.assertEqual(self.cache.get("a"), 2)
        self.cache.set("a", 3, 0)
        self.assertEqual(len(self.cache), 0)
        self.cache.set("b", 4, -1)
        self.assertEqual(len(self.cache), 0)
        self.cache.set("a", 5, 1)
        self.cache.set("a", 6)
        self.clock.now = 100
        self.assertEqual(self.cache.get("a"), 6)

    def test_none_default_delete_and_instances(self):
        self.cache.set("a", None)
        marker = object()
        self.assertIsNone(self.cache.get("a", marker))
        self.assertIs(self.cache.get("b", marker), marker)
        other = TTLCache(1, self.clock)
        self.assertEqual(len(other), 0)
        self.assertTrue(self.cache.delete("a"))
        self.assertFalse(self.cache.delete("a"))

    def test_state_machine(self):
        rng = random.Random(508)
        expected = {}
        for _ in range(180):
            self.clock.now += rng.choice([0, 0.25, 1])
            expected = {k: v for k, v in expected.items() if v[1] is None or self.clock.now < v[1]}
            key = rng.choice("abcd")
            op = rng.choice(["set", "get", "delete", "len"])
            if op == "set":
                ttl = rng.choice([None, -1, 0, 0.5, 3])
                value = rng.choice([None, 0, 1, "v"])
                expected.pop(key, None)
                if ttl is None or ttl > 0:
                    expected[key] = (value, None if ttl is None else self.clock.now + ttl)
                while len(expected) > 2:
                    expected.pop(next(iter(expected)))
                self.assertIsNone(self.cache.set(key, value, ttl))
            elif op == "get":
                result = expected.get(key, ("MISSING", None))[0]
                self.assertEqual(self.cache.get(key, "MISSING"), result)
                if key in expected:
                    value = expected.pop(key)
                    expected[key] = value
            elif op == "delete":
                had = key in expected
                expected.pop(key, None)
                self.assertIs(self.cache.delete(key), had)
            self.assertEqual(len(self.cache), len(expected))


if __name__ == "__main__":
    unittest.main()
