from pathlib import Path
from typing import Dict, List, Any
import fitz

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

def load_document(path: Path) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return [{"page_number": None, "text": text}]
    raise ValueError(f"Unsupported file type: {suffix}")

def _load_pdf(path: Path) -> List[Dict[str, Any]]:
    pages = []
    with fitz.open(str(path)) as doc:
        for idx, page in enumerate(doc):
            pages.append({
                "page_number": idx + 1,
                "text": page.get_text("text"),
            })
    return pages
