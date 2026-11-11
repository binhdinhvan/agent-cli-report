"""Regression runner: isolate legacy fixed IDs now present in real benchmark index."""
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import continue48 as cont
import retry_continue48 as retry
import test_continue48 as old_cont
import test_retry_continue48 as old_retry


def main():
    loader, runner = unittest.TestLoader(), unittest.TextTestRunner(verbosity=1)
    isolated = {
        "test_continue48": (old_cont.ContinuationTests, "test_atomic_suffix_reservation_preserves_predecessor_and_refuses_second"),
        "test_retry_continue48": (old_retry.RetryContinuationTests, "test_fresh_atomic_reservation_preserves_predecessors_and_blocks_repeat"),
    }
    suite = unittest.TestSuite()
    for path in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
        if path.stem not in isolated:
            suite.addTests(loader.loadTestsFromName(path.stem))
        else:
            cls, excluded = isolated[path.stem]
            suite.addTests(cls(name) for name in loader.getTestCaseNames(cls) if name != excluded)
    results = [runner.run(suite)]
    for module, cls, name, prior_func in [
        (cont, *isolated["test_continue48"], "prior_state"),
        (retry, *isolated["test_retry_continue48"], "predecessors"),
    ]:
        checked = getattr(module, prior_func)()
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="isolated-legacy-ids-") as temporary, \
                patch.object(cont.batch.native, "RUNTIME", pathlib.Path(temporary)), \
                patch.object(module, "ROOT", cont.SUITE / "artifacts"), \
                patch.object(module, "PROTOCOL", cont.SUITE / "artifacts/offline-protocol-placeholder.md"), \
                patch.object(module, prior_func, return_value=checked):
            results.append(runner.run(unittest.TestSuite([cls(name)])))
    print("Benchmark regression count:", sum(r.testsRun for r in results))
    raise SystemExit(not all(r.wasSuccessful() for r in results))


if __name__ == "__main__":
    main()
