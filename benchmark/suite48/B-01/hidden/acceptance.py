import json
import unittest
from test_public import load_answer

EXPECTED = {
    "default": {"value": 12, "evidence": {"defaults.py:DEFAULTS", "resolver.py:resolve"}},
    "precedence": {"value": ["cli", "env", "config", "defaults"], "evidence": {"resolver.py:resolve"}},
    "alias_trace": {"value": ["quick", "short", "timeout"], "evidence": {"aliases.py:ALIASES", "aliases.py:canonical_name"}},
    "cycle_error": {"type": "ValueError", "message": "alias cycle: loop_a", "evidence": {"aliases.py:canonical_name"}},
    "mutation": {"value": False, "evidence": {"resolver.py:resolve"}}
}


class AcceptanceTests(unittest.TestCase):
    def test_rubric(self):
        answer = load_answer()
        scores = {}
        for name, expected in EXPECTED.items():
            item = answer[name]
            keys = set(expected) - {"evidence"}
            correct = all(type(item[k]) is type(expected[k]) and item[k] == expected[k] for k in keys)
            evidence = bool(item["evidence"]) and set(item["evidence"]) <= expected["evidence"]
            scores[name] = int(correct) + int(evidence)
        print("RUBRIC_JSON=" + json.dumps({"scores": scores, "total": sum(scores.values()), "maximum": 10}), flush=True)
        self.assertEqual(sum(scores.values()), 10)


if __name__ == "__main__":
    unittest.main()
