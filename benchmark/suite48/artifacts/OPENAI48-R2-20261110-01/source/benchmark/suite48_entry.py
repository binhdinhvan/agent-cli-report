"""Trusted stdlib entrypoint inside the offline suite48 sandbox, never a paid agent."""
import json
import os
import pathlib
import resource
import runpy
import sys

resource.setrlimit(resource.RLIMIT_CPU, (12, 12))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

if sys.argv[1] == "execute":
    immutable = json.loads(pathlib.Path("/controller/immutable.json").read_text())
    readonly = {}
    for name in immutable:
        try:
            with pathlib.Path(name).open("r+"):
                readonly[name] = False
        except OSError as error:
            readonly[name] = error.errno in (13, 30)
    witness = {"readonly": readonly, "hidden_absent": not pathlib.Path("/grader").exists(),
        "real_home_absent": not pathlib.Path("/home/tts").exists(),
        "net_namespace": os.readlink("/proc/self/ns/net")}
    print("WITNESS_JSON=" + json.dumps(witness), flush=True)
    if not all(readonly.values()) or not witness["hidden_absent"] or not witness["real_home_absent"]:
        raise SystemExit(97)
    runpy.run_path("/controller/apply.py", run_name="__main__")
elif sys.argv[1] == "public":
    import unittest
    unittest.main(module="test_public", argv=["test_public", "-v"])
elif sys.argv[1] == "hidden":
    sys.argv = ["/grader/acceptance.py", "-v"]
    runpy.run_path("/grader/acceptance.py", run_name="__main__")
else:
    raise SystemExit("unknown sandbox mode")
