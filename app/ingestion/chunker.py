from typing import List, Dict, Any
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_pages(pages: List[Dict[str, Any]], chunk_size=CHUNK_SIZE,
                overlap=CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    chunks = []
    for page in pages:
        text = page["text"].strip()
        if not text:
            continue

        start = 0
        chunk_num = 1
        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Prefer a natural boundary close to the target size.
            if end < len(text):
                candidates = [text.rfind("\n\n", start, end),
                              text.rfind(". ", start, end),
                              text.rfind(" ", start, end)]
                boundary = max(candidates)
                if boundary > start + int(chunk_size * 0.55):
                    end = boundary + (2 if text[boundary:boundary+2] == "\n\n" else 1)

            piece = text[start:end].strip()
            if piece:
                chunks.append({
                    "page_number": page["page_number"],
                    "text": piece,
                    "chunk_number": chunk_num,
                })
                chunk_num += 1

            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks
