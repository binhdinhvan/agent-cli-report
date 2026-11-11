import unittest
from scheduler import task_names


class PublicTests(unittest.TestCase):
    def test_task_names(self):
        self.assertEqual(task_names({"build": ["fetch"], "fetch": []}), ["build", "fetch"])


if __name__ == "__main__":
    unittest.main()
