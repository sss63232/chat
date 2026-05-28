import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/examples", tags=["examples"])


@router.get("/sse")
async def sse_example(
    count: int = Query(default=5, ge=1, le=60),
    interval: float = Query(default=1.0, gt=0, le=10),
    stop_at: int | None = Query(default=None, ge=1, le=60),
) -> StreamingResponse:
    return StreamingResponse(
        stream_counter(count=count, interval=interval, stop_at=stop_at),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


async def stream_counter(count: int, interval: float, stop_at: int | None = None) -> AsyncIterator[str]:
    for index in range(1, count + 1):
        payload = {
            "count": index,
            "message": f"tick {index}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        yield format_sse(event="tick", data=json.dumps(payload), event_id=str(index))

        if stop_at is not None and index >= stop_at:
            interrupted_payload = {
                "count": index,
                "message": f"stream interrupted at {index}",
            }
            yield format_sse(event="interrupted", data=json.dumps(interrupted_payload), event_id=str(index))
            return

        await asyncio.sleep(interval)

    yield format_sse(event="done", data=json.dumps({"message": "stream complete"}))


def format_sse(event: str, data: str, event_id: str | None = None) -> str:
    payload = data.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    lines.extend(f"data: {line}" for line in payload.split("\n"))
    return "\n".join(lines) + "\n\n"
