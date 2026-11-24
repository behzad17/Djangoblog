import re
import unicodedata
from typing import NamedTuple


POSTAL_BOX = re.compile(
    r"^\s*(?:(?:post|p\.?\s*o\.?\s*)?box|صندوق\s*پستی)(?=\s|\d|[:.,-]|$)",
    re.IGNORECASE,
)
POSTAL_LABEL = re.compile(r"^\s*(?:postadress|postal address|(?:آدرس|نشانی)\s*پستی)\s*[:：]\s*", re.IGNORECASE)
POSTAL_NOTE = re.compile(r"(?:postadress|postal address|(?:آدرس|نشانی)\s*پستی)", re.IGNORECASE)
VISITING_LABEL = re.compile(
    r"^\s*(?:besöksadress|visiting address|(?:آدرس|نشانی)\s+(?:مراجعه|بازدید|حضوری))\s*[:：]\s*",
    re.IGNORECASE,
)
ADDRESS_LABEL = re.compile(r"^\s*(?:adress|address)\s*[:：]\s*", re.IGNORECASE)
ADDRESS_NOTE = re.compile(r"\(([^()]*)\)|\[([^\[\]]*)\]")
NOTE_SEPARATOR = re.compile(r"\s+(?:—|–|-)\s+")
SERVICE_AREA = re.compile(r"hela sverige|sverige|online|digitalt|(?:på )?distans", re.IGNORECASE)
POSTCODE = re.compile(r"^\d{3}\s?\d{2}\b")
URL_OR_EMAIL = re.compile(r"https?://|\bwww\.|@", re.IGNORECASE)

ADDRESS_HELP = (
    "نشانی مراجعه را با املای سوئدی و بدون توضیح وارد کنید. "
    "مثال: Hammarby Fabriksväg 25, plan 6, 120 30 Stockholm"
)
POSTAL_HELP = "نشانی پستی با املای سوئدی، بدون توضیح. مثال: Box 92150, 120 08 Stockholm"
NOTE_HELP = "برای نمونه، «مراجعه با هماهنگی قبلی» یا «خدمات آنلاین در سراسر سوئد»."


class AddressParts(NamedTuple):
    visiting: str
    postal: str
    note: str


def is_swedish_address(value):
    value = unicodedata.normalize("NFC", value).strip()
    value = re.sub(r"\bS:(ta?)\b", r"S\1", value, flags=re.IGNORECASE)
    return (
        bool(value)
        and value[0].isalpha()
        and not URL_OR_EMAIL.search(value)
        and not NOTE_SEPARATOR.search(value)
        and all(
            char in "0123456789 ,./-’'–\n\r\t"
            or (char.isalpha() and unicodedata.name(char, "").startswith("LATIN "))
            for char in value
        )
    )


def is_visiting_address(value):
    return (
        is_swedish_address(value)
        and not POSTAL_BOX.match(value)
        and not SERVICE_AREA.fullmatch(value.strip())
    )


def address_parts(address, postal_address="", address_note=""):
    """Separate legacy contact strings without rewriting stored records."""
    visiting, postal, notes = [], [], []
    current = visiting
    for raw in unicodedata.normalize("NFC", address).splitlines():
        line = raw.strip()
        parts = NOTE_SEPARATOR.split(line, maxsplit=1)
        line = parts[0].strip()
        line_notes = parts[1:]
        for match in ADDRESS_NOTE.finditer(line):
            line_notes.append(match.group(1) or match.group(2) or "")
        line = ADDRESS_NOTE.sub(" ", line).strip(" ,;")
        if POSTAL_LABEL.match(line) or POSTAL_BOX.match(line) or any(
            POSTAL_NOTE.fullmatch(note.strip()) for note in line_notes
        ):
            current = postal
            line = POSTAL_LABEL.sub("", line)
        elif VISITING_LABEL.match(line):
            current = visiting
            line = VISITING_LABEL.sub("", line)
        line = ADDRESS_LABEL.sub("", line).strip()
        notes.extend(note.strip() for note in line_notes if note.strip() and not POSTAL_NOTE.fullmatch(note.strip()))
        if not line:
            continue
        if SERVICE_AREA.fullmatch(line):
            notes.append(line)
        elif (POSTCODE.match(line) and current) or is_swedish_address(line):
            current.append(line)
        else:
            notes.append(line)
    return AddressParts(
        visiting=", ".join(visiting),
        postal=postal_address or ", ".join(postal),
        note=address_note or " — ".join(notes),
    )


def populate_address_initial(initial):
    parts = address_parts(
        initial.get("address") or "",
        initial.get("postal_address") or "",
        initial.get("address_note") or "",
    )
    initial.update(address=parts.visiting, postal_address=parts.postal, address_note=parts.note)
