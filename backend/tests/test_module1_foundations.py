import asyncio
import unicodedata
from collections.abc import Iterator
from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from app.schemas import (
    DocumentCreateRequest,
    DocumentReadResponse,
    PaginatedResponse,
    TextChunk,
)
from app.utils.async_helpers import (
    run_with_concurrency,
    simulate_token_stream,
    track_execution_time,
)
from app.utils.text import iter_text_chunks, normalize_text

# 1. Fixture: Dependency Injection for testing
@pytest.fixture
def sample_document() -> str:
    return (
        "Quy định nghỉ phép năm tại công ty SME Việt Nam.\r\n\r\n\r\n"
        "Nhân viên chính thức có   12 ngày phép hưởng nguyên lương mỗi năm.\n"
        "Mỗi thâm niên 5 năm được cộng thêm 1 ngày phép."
    )
    

# 2. Test pydantic v2: Normalize NFC, strip whitespace and deduplicate tags
def test_document_create_validation_and_normalization():
    nfd_title = unicodedata.normalize("NFD", "  Tài liệu Tiếng Việt  ")
    assert len(nfd_title.strip()) > len("Tài liệu Tiếng Việt")
    
    dto = DocumentCreateRequest(
        title=nfd_title,
        source_type="pdf",
        content="  Nội dung hợp đồng lao động  ",
        tags=["  HR ", "hr", "Nội Bộ", "  "],
    )
    
    assert dto.title == 'Tài liệu Tiếng Việt'
    assert unicodedata.is_normalized("NFC", dto.title)
    assert dto.tags == ['hr', 'nội bộ']
    

def test_document_create_rejects_extra_fields_and_invalid_type():
    with pytest.raises(ValidationError):
        DocumentCreateRequest(
            title="Test",
            content="Nội dung",
            unknown_field="hack", # type: ignore[call-arg]
        )
        
    with pytest.raises(ValidationError):
        DocumentCreateRequest(
            title="Test",
            source_type="excel", # type: ignore[arg-type]
            content="Nội dung",
        )
        
        
def test_generic_paginated_response_and_computed_field():
    doc=DocumentReadResponse(
        title="Chính sách bảo mật",
        source_type="markdown",
        content="Một hai ba bốn năm",
    )
    assert doc.word_count == 5
    
    page = PaginatedResponse[DocumentReadResponse](
        items=[doc],
        total=25,
        page=1,
        page_size=10,
    )
    assert page.has_next is True
    
    dumped = page.model_dump()
    assert dumped["has_next"] is True
    assert dumped["items"][0]["word_count"] == 5
    
    
# 3. Test Dataclass immutable
def test_text_chunk_is_immutable():
    chunk = TextChunk(content="Xin chào", chunk_index=0, start_char=0, end_char=8)
    assert chunk.char_count == 8
    
    with pytest.raises(FrozenInstanceError):
        chunk.content = "Sửa đổi" # type: ignore[misc]
        
    assert not hasattr(chunk, "__dict__")
    
    
# 4. Data-driven test with @pytest.mark.parametrize
@pytest.mark.parametrize(
    ("raw_text", "expected"),
    [
        ("  Xin    chào\t\tViệt Nam  ", "Xin chào Việt Nam"),
        ("Dòng 1\r\n\r\n\r\n\r\nDòng 2", "Dòng 1\n\nDòng 2"),
        ("   \n\t  ", ""),
    ]
)
def test_normalize_text(raw_text: str, expected: str):
    assert normalize_text(raw_text) == expected
    

# 5. Test Generator (yield)
def test_iter_text_chunks_is_lazy_generator(sample_document: str):
    gen = iter_text_chunks(
        sample_document,
        chunk_size=60,
        chunk_overlap=15,
        base_metadata={"source": "hr_policy.md"}
    )
    assert isinstance(gen, Iterator)
    
    chunks = list(gen)
    assert len(chunks) >= 3
    assert chunks[0].chunk_index == 0
    assert chunks[0].metadata == {"source": "hr_policy.md"}
    assert chunks[1].start_char == 45
    
    
# 6. Test Async helpers (Context Manager, Semaphore + TaskGroup, AsyncIterator)
def test_async_helpers_workflow():
    async def _run() -> None:
        async with track_execution_time("mock_llm_call") as timer:
            await asyncio.sleep(0.01)
        assert timer.operation == "mock_llm_call"
        assert timer.elapsed_ms >= 5.0
        
        active_workers = 0
        max_seen_workers = 0
        
        async def _worker(x: int) -> int:
            nonlocal active_workers, max_seen_workers
            active_workers += 1
            max_seen_workers = max(max_seen_workers, active_workers)
            await asyncio.sleep(0.01)
            active_workers -= 1
            return x * 2
        
        results = await run_with_concurrency(
            items=[1, 2, 3, 4, 5, 6],
            worker=_worker,
            max_concurrency=2,
        )
        assert results == [2, 4, 6, 8, 10, 12]
        assert max_seen_workers <= 2
        
        collected_tokens: list[str] = []
        async for token in simulate_token_stream("Docmind trợ lý AI"):
            collected_tokens.append(token)
        assert "".join(collected_tokens) == "Docmind trợ lý AI"
        assert len(collected_tokens) == 4
        
    asyncio.run(_run())