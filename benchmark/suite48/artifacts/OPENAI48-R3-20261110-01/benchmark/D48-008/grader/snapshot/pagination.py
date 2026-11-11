"""Pagination helpers."""


def merge_pages(pages):
    result = []
    positions = {}
    for page in pages:
        for record in page:
            record_id = record["id"]
            if record_id in positions:
                result[positions[record_id]] = record.copy()
            else:
                positions[record_id] = len(result)
                result.append(record.copy())
    return result
