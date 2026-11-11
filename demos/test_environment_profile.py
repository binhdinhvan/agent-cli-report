"""Offline dependency/profile validation; no key, installer, model or host binary execution."""
import copy
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import environment_profile as profiles
import preflight


class EnvironmentProfileTests(unittest.TestCase):
    def test_pinned_rg_matches_existing_package(self):
        data = profiles.environment_profile("search-r2")
        self.assertEqual(data["executables"]["rg"]["version"], "15.2.0")
        self.assertEqual(preflight.sha256(profiles.ROOT / data["executables"]["rg"]["source"]), data["executables"]["rg"]["sha256"])

    def test_all_four_profiles_mount_read_only_and_legacy_is_explicit(self):
        specs = json.loads((profiles.ROOT / "demos/artifacts/PREP-20261106-01/preparation.json").read_text())["releases"]
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="profile-tests-") as directory:
            runtime = pathlib.Path(directory)
            for spec in specs:
                for revision in ["legacy", "search-r2"]:
                    with self.subTest(tool=spec["tool"], revision=revision):
                        current = copy.deepcopy(spec)
                        current.update(config_id=spec["tool"] + revision, environment_revision=revision)
                        root = runtime / current["config_id"]
                        root.mkdir()
                        current["runtime_root"] = str(root)
                        with patch.object(preflight, "RUNTIME", runtime):
                            command, binary, env = preflight.profile(current)
                        if revision == "legacy":
                            self.assertEqual(env["PATH"], "/usr/bin:/bin")
                        else:
                            self.assertEqual(env["PATH"], "/opt/agent-cli-report-deps/search-r2/bin:/usr/bin:/bin")
                            target = command.index("/opt/agent-cli-report-deps/search-r2/bin")
                            self.assertEqual(command[target - 2], "--ro-bind")
                        self.assertIn("--unshare-net", command)

    def test_checksum_tampering_blocks_before_execution(self):
        original = json.loads((profiles.ROOT / "research/environment-profiles/search-r2.json").read_text())
        with tempfile.TemporaryDirectory(dir="/tmp/opencode", prefix="dependency-tamper-") as directory:
            root = pathlib.Path(directory)
            manifest = root / "research/environment-profiles/search-r2.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps(original))
            executable = root / ".local/environments/search-r2/bin/rg"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"synthetic invalid executable")
            executable.chmod(0o555)
            with patch.object(profiles, "ROOT", root), self.assertRaisesRegex(ValueError, "checksum mismatch"):
                profiles.environment_profile("search-r2")

    def test_unrecognized_revision_rejected(self):
        with self.assertRaises(ValueError):
            profiles.environment_profile("unreviewed-profile")


if __name__ == "__main__":
    unittest.main()
