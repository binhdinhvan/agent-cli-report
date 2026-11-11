import service

def handle_create(normalized):
    return service.create(normalized["name"])

def handle_update(normalized):
    return service.update(normalized["id"], normalized["name"])

def handle_delete(normalized):
    return service.delete(normalized["id"])
