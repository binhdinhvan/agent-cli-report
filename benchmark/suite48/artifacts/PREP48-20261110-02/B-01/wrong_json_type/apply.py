import pathlib
files = {'answer.json': '{"default": {"value": 12, "evidence": ["defaults.py:DEFAULTS"]}, "precedence": {"value": ["cli", "env", "config", "defaults"], "evidence": ["resolver.py:resolve"]}, "alias_trace": {"value": ["quick", "short", "timeout"], "evidence": ["aliases.py:ALIASES"]}, "cycle_error": {"type": "ValueError", "message": "alias cycle: loop_a", "evidence": ["aliases.py:canonical_name"]}, "mutation": {"value": 0, "evidence": ["resolver.py:resolve"]}}'}
for name, content in files.items():
    path = pathlib.Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
