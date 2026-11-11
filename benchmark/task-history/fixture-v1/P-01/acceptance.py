"""Hidden acceptance: supervisor only, never mounted into the agent workspace."""
import copy
import unittest
from intervals import merge_intervals


class AcceptanceTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(merge_intervals([]), [])

    def test_touching_is_not_overlap(self):
        self.assertEqual(merge_intervals([[0, 2], [2, 4]]), [(0, 2), (2, 4)])

    def test_nested_and_unsorted(self):
        self.assertEqual(merge_intervals([[8, 10], [2, 3], [-2, 5], [4, 7]]), [(-2, 7), (8, 10)])

    def test_no_mutation(self):
        value = [[9, 11], [1, 5], [2, 7]]
        original = copy.deepcopy(value)
        result = merge_intervals(value)
        self.assertEqual(value, original)
        self.assertEqual(result, [(1, 7), (9, 11)])

    def test_iterator_and_tuples(self):
        self.assertEqual(merge_intervals(iter([(3, 6), (1, 4)])), [(1, 6)])

    def test_duplicates(self):
        self.assertEqual(merge_intervals([[1, 3], [1, 3], [3, 4]]), [(1, 3), (3, 4)])

    def test_invalid(self):
        for value in [[[2, 2]], [[3, 1]], [[1]], [[1, 2, 3]], [["1", 2]], [[1.5, 3]], [None], [4]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                merge_intervals(value)


if __name__ == "__main__":
    unittest.main()
