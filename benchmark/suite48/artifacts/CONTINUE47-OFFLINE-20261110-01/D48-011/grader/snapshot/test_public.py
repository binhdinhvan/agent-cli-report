import unittest
from cache import TTLCache


class PublicTests(unittest.TestCase):
    def test_basic_api(self):
        c = TTLCache(2, lambda: 0)
        self.assertIsNone(c.set("a", 1))
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("missing", "default"), "default")
        self.assertEqual(len(c), 1)
        self.assertTrue(c.delete("a"))
        self.assertFalse(c.delete("a"))


if __name__ == "__main__":
    unittest.main()
