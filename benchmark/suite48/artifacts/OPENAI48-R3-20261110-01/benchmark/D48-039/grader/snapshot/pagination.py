"""Pagination helpers."""


def merge_pages(pages):
    records_by_id = {}
    for page in pages:
        for record in page:
            records_by_id[record["id"]] = dict(record)
    return list(records_by_id.values())
