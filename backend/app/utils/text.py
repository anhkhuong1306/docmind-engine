import re
import unicodedata
from collections.abc import Iterator

from app.schemas import MetadataDict, TextChunk

# 1. Remove all whitespace characters (tabs, form feeds, vertical tabs)
_MULTI_SPACES_RE = re.compile(r"[ \t\f\v]+")
# 2. Remove all newlines that are more than two in a row
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """Normalize text befor feeding into the RAG pipeline."""
    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _MULTI_SPACES_RE.sub(" ", normalized)
    normalized = _MULTI_NEWLINE_RE.sub("\n\n", normalized)
    return normalized.strip()


def iter_text_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    base_metadata: MetadataDict | None = None,
) -> Iterator[TextChunk]:
    """Lazily split text into overlapping chunks using a Generator (yield)"""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and less than chunk_size")

    cleaned = normalize_text(text)
    if not cleaned:
        return

    step = chunk_size - chunk_overlap
    text_len = len(cleaned)
    chunk_idx = 0

    for start in range(0, text_len, step):
        end = min(start + chunk_size, text_len)
        slice_text = cleaned[start:end].strip()
        if slice_text:
            yield TextChunk(
                content=slice_text,
                chunk_index=chunk_idx,
                start_char=start,
                end_char=end,
                metadata=dict(base_metadata) if base_metadata else {},
            )
            chunk_idx += 1
        if end >= text_len:
            break
