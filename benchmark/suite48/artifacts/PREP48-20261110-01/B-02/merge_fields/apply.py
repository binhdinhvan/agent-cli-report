import pathlib
files = {'pagination.py': 'def merge_pages(pages):\n    order = []\n    last = {}\n    for page in pages:\n        for record in page:\n            key = record["id"]\n            if key not in last:\n                order.append(key)\n            last.setdefault(key, {}).update(record)\n    return [last[key] for key in order]\n'}
for name, content in files.items():
    path = pathlib.Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
