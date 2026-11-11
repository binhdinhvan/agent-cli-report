"""Hidden acceptance: supervisor only, never mounted into the agent workspace."""
import copy
import unittest
from scheduler import execution_order, task_names


class AcceptanceTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(execution_order({}), [])

    def test_chain(self):
        self.assertEqual(execution_order({"test": ["build"], "fetch": [], "build": ["fetch"]}), ["fetch", "build", "test"])

    def test_available_tie_break(self):
        self.assertEqual(execution_order({"z": [], "b": [], "a": ["b"]}), ["b", "a", "z"])

    def test_diamond(self):
        self.assertEqual(execution_order({"d": ["b", "c"], "c": ["a"], "b": ["a"], "a": []}), ["a", "b", "c", "d"])

    def test_duplicates(self):
        self.assertEqual(execution_order({"b": ["a", "a"], "a": []}), ["a", "b"])

    def test_unknown(self):
        with self.assertRaises(ValueError):
            execution_order({"a": ["missing"]})

    def test_cycles(self):
        for jobs in [{"a": ["a"]}, {"a": ["b"], "b": ["a"]}, {"free": [], "a": ["b"], "b": ["a"]}]:
            with self.subTest(jobs=jobs), self.assertRaises(ValueError):
                execution_order(jobs)

    def test_no_mutation(self):
        jobs = {"c": ["b", "a", "a"], "b": [], "a": []}
        original = copy.deepcopy(jobs)
        self.assertEqual(execution_order(jobs), ["a", "b", "c"])
        self.assertEqual(jobs, original)

    def test_existing_api(self):
        self.assertEqual(task_names({"z": [], "a": []}), ["a", "z"])


if __name__ == "__main__":
    unittest.main()
