import unittest
from pagination import merge_pages


class PublicTests(unittest.TestCase):
    def test_distinct_records(self):
        self.assertEqual(merge_pages([[{"id": "b", "v": 2}], [{"id": "a", "v": 1}]]),
                         [{"id": "b", "v": 2}, {"id": "a", "v": 1}])


if __name__ == "__main__":
    unittest.main()
