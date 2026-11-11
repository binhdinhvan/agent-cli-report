import unittest
from intervals import merge_intervals


class PublicTests(unittest.TestCase):
    def test_overlap(self):
        self.assertEqual(merge_intervals([[1, 4], [2, 6], [9, 10]]), [(1, 6), (9, 10)])


if __name__ == "__main__":
    unittest.main()
