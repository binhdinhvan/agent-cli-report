import pathlib
files = {'answer.json': '{"precedence": {"value": ["cli", "env", "config", "defaults"], "evidence": ["resolver.py:resolve"]}, "alias_trace": {"value": ["quick", "short", "timeout"], "evidence": ["aliases.py:ALIASES"]}, "cycle_error": {"type": "ValueError", "message": "alias cycle: loop_a", "evidence": ["aliases.py:canonical_name"]}, "mutation": {"value": false, "evidence": ["resolver.py:resolve"]}}'}
for name, content in files.items():
    path = pathlib.Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
