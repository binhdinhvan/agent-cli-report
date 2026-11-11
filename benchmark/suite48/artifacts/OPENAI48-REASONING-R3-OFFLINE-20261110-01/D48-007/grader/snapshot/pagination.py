def merge_pages(pages):
    order = []
    last = {}
    for page in pages:
        for record in page:
            key = record["id"]
            if key not in last:
                order.append(key)
            last[key] = dict(record)
    return [last[key] for key in order]
