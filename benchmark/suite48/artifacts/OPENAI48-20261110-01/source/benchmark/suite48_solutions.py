"""Supervisor-authored reference/mutants for offline acceptance. Never expose to agents."""
import json
from suite48_runtime import SUITE

B02 = '''def merge_pages(pages):
    order = []
    last = {}
    for page in pages:
        for record in page:
            key = record["id"]
            if key not in last:
                order.append(key)
            last[key] = dict(record)
    return [last[key] for key in order]
'''

B03 = '''from collections import OrderedDict

class TTLCache:
    def __init__(self, capacity, clock):
        self.capacity = capacity
        self.clock = clock
        self.entries = OrderedDict()

    def _purge(self):
        now = self.clock()
        for key, (_, deadline) in list(self.entries.items()):
            if deadline is not None and now >= deadline:
                del self.entries[key]

    def set(self, key, value, ttl=None):
        self._purge()
        self.entries.pop(key, None)
        if ttl is not None and ttl <= 0:
            return None
        deadline = None if ttl is None else self.clock() + ttl
        self.entries[key] = (value, deadline)
        while len(self.entries) > self.capacity:
            self.entries.popitem(last=False)
        return None

    def get(self, key, default=None):
        self._purge()
        if key not in self.entries:
            return default
        self.entries.move_to_end(key)
        return self.entries[key][0]

    def delete(self, key):
        self._purge()
        if key not in self.entries:
            return False
        del self.entries[key]
        return True

    def __len__(self):
        self._purge()
        return len(self.entries)
'''

VALIDATION = '''from models import PayloadError

def validate_payload(command, payload):
    if command not in ("create", "update", "delete"):
        raise ValueError("unknown command: " + command)
    if not isinstance(payload, dict):
        raise PayloadError("payload must be a dictionary")
    normalized = {}
    if command in ("update", "delete"):
        identifier = payload.get("id")
        if type(identifier) is not int or identifier <= 0:
            raise PayloadError("id must be positive integer")
        normalized["id"] = identifier
    if command in ("create", "update"):
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            raise PayloadError("name must be nonempty string")
        normalized["name"] = name.strip()
    return normalized
'''
HANDLERS = '''import service

def handle_create(normalized):
    return service.create(normalized["name"])

def handle_update(normalized):
    return service.update(normalized["id"], normalized["name"])

def handle_delete(normalized):
    return service.delete(normalized["id"])
'''
ROUTER = '''from routing import validation, handlers

def dispatch(command, payload):
    normalized = validation.validate_payload(command, payload)
    return getattr(handlers, "handle_" + command)(normalized)
'''


def answer():
    return {
        "default": {"value": 12, "evidence": ["defaults.py:DEFAULTS"]},
        "precedence": {"value": ["cli", "env", "config", "defaults"], "evidence": ["resolver.py:resolve"]},
        "alias_trace": {"value": ["quick", "short", "timeout"], "evidence": ["aliases.py:ALIASES"]},
        "cycle_error": {"type": "ValueError", "message": "alias cycle: loop_a", "evidence": ["aliases.py:canonical_name"]},
        "mutation": {"value": False, "evidence": ["resolver.py:resolve"]}}


def references():
    return {"B-01": {"answer.json": json.dumps(answer()) + "\n"},
        "B-02": {"pagination.py": B02}, "B-03": {"cache.py": B03},
        "B-04": {"router.py": ROUTER, "routing/__init__.py": "", "routing/validation.py": VALIDATION,
                 "routing/handlers.py": HANDLERS}}


def variants(task_id):
    reference = references()[task_id]
    cases = {"baseline": {}, "reference": reference}

    def change(label, name, old, new):
        if old not in reference[name]:
            raise ValueError("Mutant source did not match")
        cases[label] = {**reference, name: reference[name].replace(old, new)}

    if task_id == "B-01":
        for field in answer():
            changed = answer()
            if field == "cycle_error":
                changed[field]["message"] = "wrong"
            elif field == "mutation":
                changed[field]["value"] = True
            elif field in ("precedence", "alias_trace"):
                changed[field]["value"] = list(reversed(changed[field]["value"]))
            else:
                changed[field]["value"] = 13
            cases["wrong_value_" + field] = {"answer.json": json.dumps(changed)}
            changed = answer()
            changed[field]["evidence"] = ["missing.py:missing"]
            cases["wrong_evidence_" + field] = {"answer.json": json.dumps(changed)}
        changed = answer()
        del changed["default"]
        cases["missing_field"] = {"answer.json": json.dumps(changed)}
        cases["duplicate_keys"] = {"answer.json": '{"x": 1, "x": 2}'}
        changed = answer()
        changed["mutation"]["value"] = 0
        cases["wrong_json_type"] = {"answer.json": json.dumps(changed)}
        changed = answer()
        changed["unexpected"] = {}
        cases["unknown_field"] = {"answer.json": json.dumps(changed)}
        cases["nonfinite_number"] = {"answer.json": json.dumps(answer()).replace('"value": 12', '"value": NaN')}
    elif task_id == "B-02":
        change("sort_ids", "pagination.py", "for key in order]", "for key in sorted(order)]")
        change("no_copy", "pagination.py", "dict(record)", "record")
        change("merge_fields", "pagination.py", "last[key] = dict(record)", "last.setdefault(key, {}).update(record)")
        change("first_duplicate_wins", "pagination.py", "last[key] = dict(record)", "last.setdefault(key, dict(record))")
        change("mutate_input", "pagination.py", "key = record[\"id\"]", "key = record[\"id\"]\n            record['injected'] = True")
        change("generator_consumed_twice", "pagination.py", "order = []", "list(pages)\n    order = []")
    elif task_id == "B-03":
        change("wrong_expiry_equality", "cache.py", "now >= deadline", "now > deadline")
        change("expiry_ignored", "cache.py", "now >= deadline", "False")
        change("fifo_not_lru", "cache.py", "self.entries.move_to_end(key)", "pass")
        change("mru_eviction", "cache.py", "popitem(last=False)", "popitem(last=True)")
        cases["nonpositive_ttl_persists"] = {"cache.py": B03.replace("ttl <= 0", "False").replace(
            "None if ttl is None else self.clock() + ttl", "None if ttl is None or ttl <= 0 else self.clock() + ttl")}
        change("overwrite_deadline_wrong", "cache.py", "deadline = None if ttl is None else self.clock() + ttl", "deadline = self.clock() + 1")
        change("len_includes_expired", "cache.py", "def __len__(self):\n        self._purge()", "def __len__(self):\n        pass")
    else:
        cases["valid_alias_imports"] = {**reference, "router.py": '''from routing.validation import validate_payload as validate
from routing.handlers import handle_create, handle_update, handle_delete

def dispatch(command, payload):
    normalized = validate(command, payload)
    if command == "create":
        return handle_create(normalized)
    if command == "update":
        return handle_update(normalized)
    return handle_delete(normalized)
'''}
        cases["valid_handler_registry"] = {**reference, "router.py": '''from routing.validation import validate_payload
from routing.handlers import handle_create, handle_update, handle_delete
HANDLERS = {"create": handle_create, "update": handle_update, "delete": handle_delete}

def dispatch(command, payload):
    normalized = validate_payload(command, payload)
    return HANDLERS[command](normalized)
'''}
        cases["unused_extraction"] = {**reference, "router.py": (SUITE / "B-04/fixture/router.py").read_text()}
        change("wrong_normalization", "routing/validation.py", 'normalized["name"] = name.strip()', 'normalized["name"] = name')
        change("bool_id_accepted", "routing/validation.py", "type(identifier) is not int", "not isinstance(identifier, int)")
        change("mutate_payload", "routing/validation.py", "normalized = {}", "normalized = payload")
        change("import_side_effect", "routing/handlers.py", "import service", "import service\nprint('side effect')")
        change("wrong_handler", "routing/handlers.py", 'service.delete(normalized["id"])', 'service.delete(999)')
    return cases


def writer_source(files):
    """This trusted writer runs only inside bwrap; it is not output of any model."""
    return "import pathlib\nfiles = " + repr(files) + "\nfor name, content in files.items():\n    path = pathlib.Path(name)\n    path.parent.mkdir(parents=True, exist_ok=True)\n    path.write_text(content)\n"
