import re
import unicodedata


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


ADDRESS_HELP = (
    "فقط نام خیابان، شماره، طبقه (در صورت نیاز)، کد پستی و شهر را با املای سوئدی وارد کنید. "
    "مثال: Hammarby Fabriksväg 25, plan 6, 120 30 Stockholm"
)
ADDRESS_LABEL = re.compile(r"^\s*(?:postadress|postal address|adress|address)\s*[:：]\s*", re.IGNORECASE)
ADDRESS_NOTE = re.compile(r"\([^()]*\)|\[[^\[\]]*\]")
URL_OR_EMAIL = re.compile(r"https?://|\bwww\.|@", re.IGNORECASE)


def _address_character(char):
    return char in "0123456789 ,./-’'–\n\r\t" or (
        char.isalpha() and unicodedata.name(char, "").startswith("LATIN ")
    )


def is_swedish_address(value):
    value = unicodedata.normalize("NFC", value)
    return (
        bool(value.strip())
        and value[0].isalpha()
        and not URL_OR_EMAIL.search(value)
        and all(_address_character(char) for char in value)
    )


def address_for_display(value):
    """Render older addresses with their annotations and non-Latin text removed."""
    lines = []
    for line in unicodedata.normalize("NFC", value).splitlines():
        line = ADDRESS_LABEL.sub("", VISITING_LABEL.sub("", line))
        line = ADDRESS_NOTE.sub(" ", line)
        if URL_OR_EMAIL.search(line):
            continue
        line = "".join(char if _address_character(char) else " " for char in line)
        line = re.sub(r"\s+", " ", line).strip(" ,./-–")
        if line:
            lines.append(line)
    return ", ".join(lines)


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
    return address_for_display("\n".join(visiting_lines))
