"""Offline sandbox/scope regression; no model/key/native CLI invocation."""
import pathlib
import shutil
import tempfile
import unittest

from suite48_runtime import SUITE, grade, passed, sandbox
from suite48_solutions import references, variants, writer_source


class Suite48Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="suite48-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)

    def project(self, task="B-02"):
        project = self.root / "project"
        shutil.copytree(SUITE / task / "fixture", project)
        return project

    def test_reference_files_fit_scope(self):
        import json
        manifest = json.loads((SUITE / "manifest.json").read_text())
        for task in manifest["tasks"]:
            self.assertLessEqual(set(references()[task["id"]]), set(task["allowed_changes"]))
            self.assertIn("baseline", variants(task["id"]))

    def test_forbidden_change_deletion_and_new_file_fail(self):
        project = self.project()
        for index, action in enumerate(["test", "delete", "new"]):
            if action == "test":
                (project / "test_public.py").write_text("pass\n")
            elif action == "delete":
                (project / "pagination.py").unlink()
            else:
                (project / "unexpected.py").write_text("pass\n")
            result = grade(project, "B-02", self.root / f"grade{index}")
            self.assertFalse(result["scope_ok"])
            self.assertEqual(result["suites"], {})

    def test_symlink_and_fifo_rejected_without_reading_target(self):
        import os
        project = self.project()
        (project / "outside").symlink_to("/etc/passwd")
        os.mkfifo(project / "pipe")
        result = grade(project, "B-02", self.root / "grade")
        self.assertFalse(result["pass"])
        self.assertEqual(set(result["invalid_paths"]), {"outside", "pipe"})

    def test_allowed_additions_work_for_refactor(self):
        project = self.project("B-04")
        writer = self.root / "apply.py"
        writer.write_text(writer_source(references()["B-04"]))
        execution = sandbox(project, "B-04", "execute", writer)
        self.assertTrue(passed(execution), execution)
        result = grade(project, "B-04", self.root / "grade")
        self.assertTrue(result["pass"], result)

    def test_readonly_hidden_absent_network_and_timeout(self):
        project = self.project()
        writer = self.root / "apply.py"
        writer.write_text("import pathlib\nassert not pathlib.Path('/grader').exists()\n")
        execution = sandbox(project, "B-02", "execute", writer)
        self.assertTrue(passed(execution), execution)
        self.assertTrue(all(execution["witness"]["readonly"].values()))
        self.assertNotEqual(execution["witness"]["net_namespace"], execution["host_net_namespace"])
        writer.write_text("while True: pass\n")
        execution = sandbox(project, "B-02", "execute", writer, timeout=0.3)
        self.assertTrue(execution["timed_out"])

    def test_readonly_write_and_output_limit_fail(self):
        project = self.project()
        writer = self.root / "apply.py"
        writer.write_text("open('test_public.py', 'w').write('bad')\n")
        self.assertFalse(passed(sandbox(project, "B-02", "execute", writer)))
        self.assertEqual((project / "test_public.py").read_bytes(), (SUITE / "B-02/fixture/test_public.py").read_bytes())
        writer.write_text("import os\nwhile True: os.write(1, b'x'*65536)\n")
        self.assertFalse(passed(sandbox(project, "B-02", "execute", writer)))


if __name__ == "__main__":
    unittest.main()
