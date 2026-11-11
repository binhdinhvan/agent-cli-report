"""Public answer schema; no expected answers are embedded here."""
import json
import pathlib
import unittest


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_answer():
    text = pathlib.Path("answer.json").read_text()
    answer = json.loads(text, object_pairs_hook=unique_object,
                        parse_constant=lambda text: (_ for _ in ()).throw(ValueError(text)))
    fields = {"default", "precedence", "alias_trace", "cycle_error", "mutation"}
    if type(answer) is not dict or set(answer) != fields:
        raise ValueError("expected exactly five fields")
    for name, item in answer.items():
        expected = {"type", "message", "evidence"} if name == "cycle_error" else {"value", "evidence"}
        if type(item) is not dict or set(item) != expected:
            raise ValueError("invalid item fields")
        evidence = item["evidence"]
        if type(evidence) is not list or not evidence or not all(type(v) is str and v.count(":") == 1 for v in evidence):
            raise ValueError("expected nonempty evidence list of path:symbol")
        if name in ("precedence", "alias_trace") and (type(item["value"]) is not list or not all(type(v) is str for v in item["value"])):
            raise ValueError("expected string array")
        if name == "mutation" and type(item["value"]) is not bool:
            raise ValueError("expected boolean")
        if name == "default" and type(item["value"]) not in (int, float, str, bool, type(None)):
            raise ValueError("expected scalar JSON value")
        if name == "cycle_error" and not all(type(item[k]) is str for k in ("type", "message")):
            raise ValueError("expected exception strings")
    return answer


class PublicTests(unittest.TestCase):
    def test_schema(self):
        load_answer()


if __name__ == "__main__":
    unittest.main()
