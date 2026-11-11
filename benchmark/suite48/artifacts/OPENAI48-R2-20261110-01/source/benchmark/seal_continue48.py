"""Create separate rubric revision; never edit the original sealed suite."""
import json
import shutil

import batch48 as batch

REV = batch.SUITE / "revisions/b01-evidence-r2"


def main():
    old_inputs = batch.inputs()  # Original native/seal/baseline verifier, read-only.
    REV.mkdir(parents=True, exist_ok=False)
    shutil.copy2(batch.SUITE / "manifest.json", REV / "manifest.json")
    for task in ("B-01", "B-02", "B-03", "B-04"):
        shutil.copytree(batch.SUITE / task, REV / task)
    (REV / "B-01/hidden/acceptance.py").write_bytes((batch.ROOT / "benchmark/rubric_b01_r2.py").read_bytes())
    files = {str(p.relative_to(REV)): batch.digest(p) for p in sorted(REV.rglob("*")) if p.is_file()}
    changed = [name for name, value in files.items() if value != batch.digest(batch.SUITE / name)]
    assert changed == ["B-01/hidden/acceptance.py"], changed
    batch.native.write(REV / "seal.json", {"revision": "b01-evidence-r2", "created_at_utc": batch.native.now(),
        "changed_from_r1": changed, "files_sha256": files, "original_input_sha256": old_inputs,
        "scope": "Rubric revision only; not native/model acceptance or launch approval"})
    print("Created separate r2 seal; original suite untouched")


if __name__ == "__main__":
    main()
