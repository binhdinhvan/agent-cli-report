import unittest
from models import PayloadError
from router import dispatch


class PublicTests(unittest.TestCase):
    def test_create(self):
        self.assertEqual(dispatch("create", {"name": " A "}), {"action": "created", "name": "A"})

    def test_update(self):
        self.assertEqual(dispatch("update", {"id": 3, "name": " B "}), {"action": "updated", "id": 3, "name": "B"})

    def test_delete(self):
        self.assertEqual(dispatch("delete", {"id": 2}), {"action": "deleted", "id": 2})

    def test_validation(self):
        with self.assertRaisesRegex(PayloadError, "id must be positive integer"):
            dispatch("update", {"id": 0, "name": "A"})


if __name__ == "__main__":
    unittest.main()
