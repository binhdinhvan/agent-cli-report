import ast
import contextlib
import copy
import importlib
import inspect
import io
import pathlib
import sys
import unittest
import original_router
import router


def outcome(function, command, payload):
    before = copy.deepcopy(payload)
    try:
        result = ("return", function(command, payload))
    except Exception as error:
        result = ("raise", type(error).__name__, str(error))
    return result, payload == before


class AcceptanceTests(unittest.TestCase):
    def test_behavior_corpus(self):
        payloads = [None, [], "bad", {}, {"id": True}, {"id": -1}, {"id": 1.0},
                    {"id": 2}, {"name": ""}, {"name": 0}, {"name": " \t"},
                    {"id": 3, "name": "ok"}, {"id": 0, "name": ""},
                    {"id": 8, "name": "  Café\t", "extra": [1]}, {"name": "a"}]
        for command in ("create", "update", "delete", "missing", ""):
            for payload in payloads:
                with self.subTest(command=command, payload=payload):
                    self.assertEqual(outcome(router.dispatch, command, copy.deepcopy(payload)),
                                     outcome(original_router.dispatch, command, copy.deepcopy(payload)))
        self.assertEqual(list(inspect.signature(router.dispatch).parameters), ["command", "payload"])

    def test_extracted_functions(self):
        validation = importlib.import_module("routing.validation")
        handlers = importlib.import_module("routing.handlers")
        for command, payload in [("create", {"name": " A "}), ("update", {"id": 2, "name": " B "}), ("delete", {"id": 4})]:
            normalized = validation.validate_payload(command, payload)
            before = copy.deepcopy(payload)
            self.assertIsNot(normalized, payload)
            self.assertEqual(payload, before)
            self.assertEqual(getattr(handlers, "handle_" + command)(normalized), original_router.dispatch(command, payload))
        for command, payload in [("unknown", None), ("update", {}), ("create", {"name": ""}), ("delete", [])]:
            self.assertEqual(outcome(validation.validate_payload, command, payload),
                             outcome(original_router.dispatch, command, payload))

    def test_delegation_not_unused_modules(self):
        validation = importlib.import_module("routing.validation")
        handlers = importlib.import_module("routing.handlers")
        for command in ("create", "update", "delete"):
            calls, returned = [], {}
            validate = validation.validate_payload
            handler = getattr(handlers, "handle_" + command)

            def profile(frame, event, arg):
                for label, function in (("validation", validate), ("handler", handler)):
                    if frame.f_code is function.__code__:
                        if event == "call":
                            names = list(inspect.signature(function).parameters)
                            calls.append((label, [frame.f_locals.get(name) for name in names]))
                        elif event == "return":
                            returned[label] = arg

            payload = {"id": 3, "name": " A "}
            old_profile = sys.getprofile()
            try:
                sys.setprofile(profile)
                result = router.dispatch(command, payload)
            finally:
                sys.setprofile(old_profile)
            # Trace actual calls instead of monkeypatching names: supports aliases,
            # cached handler registries and module imports without a style preference.
            self.assertEqual([label for label, _ in calls], ["validation", "handler"])
            self.assertEqual(calls[0][1], [command, payload])
            self.assertIs(calls[1][1][0], returned["validation"])
            self.assertEqual(result, returned["handler"])

    def test_module_structure_and_import_quiet(self):
        for name in ("routing/__init__.py", "routing/validation.py", "routing/handlers.py"):
            path = pathlib.Path(name)
            self.assertTrue(path.is_file())
            ast.parse(path.read_text())
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            for module in ("routing", "routing.validation", "routing.handlers"):
                importlib.reload(importlib.import_module(module))
        self.assertEqual(stream.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
