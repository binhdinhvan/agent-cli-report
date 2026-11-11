"""Tests fixture nghiên cứu, không test native tool/provider behavior."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

WORKER = Path(__file__).resolve().parent / "fixtures/background_worker.py"


class BackgroundFixtureTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, "-I", "-B", str(WORKER), *args],
                              capture_output=True, text=True, timeout=6)

    def rows(self, text):
        return [json.loads(line) for line in text.splitlines()]

    def test_success_and_order(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        rows = self.rows(result.stdout)
        self.assertEqual([r["event"] for r in rows], ["ready", "progress", "progress", "progress", "completed"])
        self.assertEqual([r["seq"] for r in rows], list(range(5)))
        self.assertEqual([r["elapsed_ms"] for r in rows], sorted(r["elapsed_ms"] for r in rows))
        self.assertEqual(rows[-1]["marker"], "fixture-r1")

    def test_error_is_intentional(self):
        result = self.invoke("--mode", "error", "--steps", "1")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(self.rows(result.stdout)[-1]["event"], "error")

    def test_zero_steps_rejected(self):
        result = self.invoke("--steps", "0")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_unbounded_steps_rejected(self):
        result = self.invoke("--steps", "31")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_mode_rejected(self):
        result = self.invoke("--mode", "unknown")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    @unittest.skipUnless(os.name == "posix", "SIGTERM fixture acceptance is POSIX-only")
    def test_cancel_own_child(self):
        child = subprocess.Popen([sys.executable, "-I", "-B", str(WORKER), "--steps", "30"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            # Sleep budget worker3s; test có deadline riêng nếu ready event thiếu.
            import selectors
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                self.assertTrue(selector.select(timeout=4), "missing fixture ready")
            first = child.stdout.readline()
            self.assertEqual(json.loads(first)["event"], "ready")
            child.terminate()  # Chỉ PID Popen do chính test tạo.
            rest, errors = child.communicate(timeout=4)
            self.assertEqual(child.returncode, 143)
            self.assertEqual(errors, "")
            self.assertEqual(self.rows(first + rest)[-1]["event"], "cancelled")
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=4)
            child.stdout.close()
            child.stderr.close()


if __name__ == "__main__":
    unittest.main()
