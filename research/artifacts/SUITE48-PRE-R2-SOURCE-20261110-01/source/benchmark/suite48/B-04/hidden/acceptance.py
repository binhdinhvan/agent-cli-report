import ast
import contextlib
import copy
import importlib
import inspect
import io
import pathlib
import unittest
from unittest.mock import Mock, patch
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
            normalized, payload, result = {"sentinel": True}, {"raw": True}, object()
            original_validate = validation.validate_payload
            original_handler = getattr(handlers, "handle_" + command)
            validate = Mock(return_value=normalized)
            handler = Mock(return_value=result)
            with contextlib.ExitStack() as stack:
                # Accept module imports and direct from-import aliases alike.
                for name, value in list(vars(router).items()):
                    if value is original_validate:
                        stack.enter_context(patch.object(router, name, validate))
                    if value is original_handler:
                        stack.enter_context(patch.object(router, name, handler))
                stack.enter_context(patch.object(validation, "validate_payload", validate))
                stack.enter_context(patch.object(handlers, "handle_" + command, handler))
                self.assertIs(router.dispatch(command, payload), result)
                validate.assert_called_once_with(command, payload)
                handler.assert_called_once_with(normalized)

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
