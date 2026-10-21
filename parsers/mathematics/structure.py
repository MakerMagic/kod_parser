"""Traversal of ordered RAW content, including source-evidenced list items."""


def walk(blocks):
    for block in blocks:
        yield block
        if block["type"] == "list":
            for item in block["items"]:
                yield from walk(item["content"])
