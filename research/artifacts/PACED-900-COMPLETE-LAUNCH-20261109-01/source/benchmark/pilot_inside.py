"""Witness writable pilot trước CLI, sau đó dùng bridge đã kiểm chứng."""
import json
import os
import pathlib
import sys

root = pathlib.Path.cwd().parent
probe = pathlib.Path(".pilot-write-witness")
probe.write_text("offline writable witness\n")
probe.unlink()
try:
    with pathlib.Path("test_public.py").open("r+"):
        test_read_only = False
except PermissionError:
    test_read_only = True
except OSError as error:
    test_read_only = error.errno == 30
witness = {"project_writable": True, "public_test_read_only": test_read_only,
           "hidden_grader_absent": not pathlib.Path("/grader").exists(),
           "real_home_hidden": not pathlib.Path("/home/tts").exists(),
           "net_namespace": os.readlink("/proc/self/ns/net")}
(root / "pilot-witness.json").write_text(json.dumps(witness, indent=2))
if not all(witness[k] for k in ["project_writable", "public_test_read_only", "hidden_grader_absent", "real_home_hidden"]):
    sys.exit(97)
import inside
inside.main()
