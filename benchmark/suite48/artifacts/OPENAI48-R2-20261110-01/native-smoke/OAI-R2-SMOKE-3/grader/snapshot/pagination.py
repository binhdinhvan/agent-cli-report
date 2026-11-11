"""Pagination helpers."""


def merge_pages(pages):
    result = []
    seen = set()
    for page in pages:
        for record in page:
            if record["id"] not in seen:
                seen.add(record["id"])
                result.append(record)
    return result
