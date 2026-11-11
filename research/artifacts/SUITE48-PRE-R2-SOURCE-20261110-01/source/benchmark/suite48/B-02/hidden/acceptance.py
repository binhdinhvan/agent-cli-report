import copy
import random
import unittest
from pagination import merge_pages


class AcceptanceTests(unittest.TestCase):
    def test_empty(self):
        for pages in ([], [[], []], iter([]), (iter(()) for _ in range(2))):
            self.assertEqual(merge_pages(pages), [])

    def test_duplicate_replaces_not_merges(self):
        self.assertEqual(merge_pages([[{"id": "b", "old": 0}, {"id": "a"}, {"id": "b", "new": 1}],
                                     [{"id": "c"}, {"id": "a", "v": 3}]]),
                         [{"id": "b", "new": 1}, {"id": "a", "v": 3}, {"id": "c"}])

    def test_one_shot(self):
        def pages():
            yield (r for r in [{"id": "a", "v": 1}, {"id": "b"}])
            yield (r for r in [{"id": "a", "v": 2}])
        self.assertEqual(merge_pages(pages()), [{"id": "a", "v": 2}, {"id": "b"}])

    def test_no_mutation_and_shallow_copy(self):
        nested = []
        data = [[{"id": "b", "nested": nested}, {"id": "a"}]]
        before = copy.deepcopy(data)
        result = merge_pages(data)
        self.assertEqual(data, before)
        self.assertIsNot(result[0], data[0][0])
        self.assertIs(result[0]["nested"], nested)
        result[0]["extra"] = True
        self.assertNotIn("extra", data[0][0])
        self.assertEqual(merge_pages([]), [])
        self.assertEqual(merge_pages([[{"id": "b"}]]), [{"id": "b"}])

    def test_randomized_contract(self):
        rng = random.Random(731)
        for _ in range(60):
            pages = [[{"id": rng.choice("abcde"), "v": rng.randrange(100)}
                      for _ in range(rng.randrange(8))] for _ in range(rng.randrange(6))]
            order, last = [], {}
            for page in pages:
                for item in page:
                    if item["id"] not in last:
                        order.append(item["id"])
                    last[item["id"]] = dict(item)
            expected = [last[key] for key in order]
            before = copy.deepcopy(pages)
            self.assertEqual(merge_pages(pages), expected)
            self.assertEqual(pages, before)


if __name__ == "__main__":
    unittest.main()
