"""Pure service functions: no persistence or external I/O."""


def create(name):
    return {"action": "created", "name": name}


def update(identifier, name):
    return {"action": "updated", "id": identifier, "name": name}


def delete(identifier):
    return {"action": "deleted", "id": identifier}
