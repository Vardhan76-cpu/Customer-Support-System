import re
from typing import List, Dict, Any


def clean_text(text: str) -> str:
    """
    Clean extracted document text while preserving
    meaningful paragraph and sentence structure.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove null characters
    text = text.replace("\x00", "")

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Remove excessive spaces
    text = re.sub(r"[ ]{2,}", " ", text)

    # Reduce excessive blank lines
    text = re.sub(r"\n[ ]*\n[ ]*\n+", "\n\n", text)

    # Remove spaces at the beginning/end of lines
    lines = [
        line.strip()
        for line in text.split("\n")
    ]

    text = "\n".join(lines)

    # Final cleanup
    text = re.sub(r" +", " ", text)

    return text.strip()


def clean_pages(
    pages: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Clean every page returned by the document loader.

    Expected input:

    [
        {
            "page_number": 1,
            "text": "some extracted text"
        },
        ...
    ]

    Returns the same structure with cleaned text.
    """

    cleaned_pages = []

    for page in pages:

        if not isinstance(page, dict):
            continue

        page_number = page.get(
            "page_number",
            len(cleaned_pages) + 1,
        )

        text = page.get(
            "text",
            "",
        )

        cleaned_text = clean_text(text)

        if not cleaned_text:
            continue

        cleaned_pages.append(
            {
                "page_number": page_number,
                "text": cleaned_text,
            }
        )

    return cleaned_pages