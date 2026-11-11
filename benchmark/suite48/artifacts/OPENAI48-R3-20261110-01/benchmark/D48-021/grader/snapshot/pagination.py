"""Pagination helpers."""


def merge_pages(pages):
    result = []
    positions = {}
    for page in pages:
        for record in page:
            record_id = record["id"]
            copied_record = dict(record)
            if record_id in positions:
                result[positions[record_id]] = copied_record
            else:
                positions[record_id] = len(result)
                result.append(copied_record)
    return result
