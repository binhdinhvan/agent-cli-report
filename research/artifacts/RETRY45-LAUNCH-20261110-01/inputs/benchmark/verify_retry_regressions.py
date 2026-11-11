"""Run offline suites, isolating fixed legacy test IDs from now-populated real CSV."""
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import continue48 as cont
import test_continue48 as legacy


def main():
    loader, runner = unittest.TestLoader(), unittest.TextTestRunner(verbosity=1)
    main_suite = unittest.TestSuite(loader.loadTestsFromName(p.stem)
        for p in sorted(pathlib.Path(__file__).parent.glob("test_*.py")) if p.stem != "test_continue48")
    atomic = "test_atomic_suffix_reservation_preserves_predecessor_and_refuses_second"
    for name in loader.getTestCaseNames(legacy.ContinuationTests):
        if name != atomic:
            main_suite.addTest(legacy.ContinuationTests(name))
    first = runner.run(main_suite)
    verified_prior = cont.prior_state()
    with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="legacy-reservation-regression-") as temporary, \
            patch.object(cont.batch.native, "RUNTIME", pathlib.Path(temporary)), \
            patch.object(cont, "ROOT", cont.SUITE / "artifacts"), \
            patch.object(cont, "PROTOCOL", cont.SUITE / "artifacts/offline-protocol-placeholder.md"), \
            patch.object(cont, "prior_state", return_value=verified_prior):
        # Artifact tempfile stays within this replacement ROOT; no real CSV is consulted.
        last = runner.run(unittest.TestSuite([legacy.ContinuationTests(atomic)]))
    print("Benchmark regression count:", first.testsRun + last.testsRun)
    raise SystemExit(not (first.wasSuccessful() and last.wasSuccessful()))


if __name__ == "__main__":
    main()
