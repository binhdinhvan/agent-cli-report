import pathlib
files = {'answer.json': '{"x": 1, "x": 2}'}
for name, content in files.items():
    path = pathlib.Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
