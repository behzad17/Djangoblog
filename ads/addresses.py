import re


POSTAL_ADDRESS = re.compile(
    r"(?:آدرس|نشانی)\s*پستی|\bpostadress\b|\bpostal address\b",
    re.IGNORECASE,
)
POSTAL_BOX = re.compile(
    r"^\s*(?:(?:post|p\.?\s*o\.?\s*)?box|صندوق\s*پستی)(?=\s|\d|[:.,-]|$)",
    re.IGNORECASE,
)
VISITING_LABEL = re.compile(
    r"^\s*(?:besöksadress|visiting address|(?:آدرس|نشانی)\s+(?:مراجعه|بازدید|حضوری))\s*[:：]\s*",
    re.IGNORECASE,
)


def visiting_destination(address):
    """Extract a map destination from existing free-form directory addresses."""
    visiting_lines = []
    in_postal_block = False
    for line in address.splitlines():
        line = line.strip()
        if VISITING_LABEL.match(line):
            if visiting_lines:
                break
            in_postal_block = False
            line = VISITING_LABEL.sub("", line)
        if POSTAL_ADDRESS.search(line) or POSTAL_BOX.match(line):
            in_postal_block = True
        if line and not in_postal_block:
            visiting_lines.append(line.strip(" ,;"))
    if not visiting_lines or re.match(r"^\d{3}\s?\d{2}\b", visiting_lines[0]):
        return ""
    return ", ".join(visiting_lines)
