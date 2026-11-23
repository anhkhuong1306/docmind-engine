import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass(slots=True)
class TimingResult:
    """Store execution time of an async block for logging/observability."""
    
    operation: str
    elapsed_ms: float = 0.0
    
    
@asynccontextmanager
async def track_execution_time(operation: str) -> AsyncIterator[TimingResult]:
    """Async context manager to measure latency of LLM or vector DB calls."""
    result = TimingResult(operation=operation)
    start = time.perf_counter()
    try:
        yield result
    finally:
        result.elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        

async def run_with_concurrency[T, R] (
    items: list[T],
    worker: Callable[[T], Awaitable[R]],
    max_concurrency: int = 5,
) -> list[R]:
    """Run async tasks conccurrently with a concurrency limit."""
    if max_concurrency <= 0:
        raise ValueError("max_concurrency must be greater than 0")
    if not items:
        return []
    
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def _bounded_worker(item: T) -> R:
        async with semaphore:
            return await worker(item)
        
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(_bounded_worker(item)) for item in items]
        
    return [t.result() for t in tasks]


async def simulate_token_stream(text: str, delay_seconds: float = 0.0) -> AsyncIterator[str]:
    """Async Generator simulating how an LLM streams tokens over SSE."""
    words = text.split(" ")
    for i, word in enumerate(words):
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        suffix = " " if i < len(words) - 1 else ""
        yield f"{word}{suffix}"
        