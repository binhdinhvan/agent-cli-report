import pathlib
files = {}
for name, content in files.items():
    path = pathlib.Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
