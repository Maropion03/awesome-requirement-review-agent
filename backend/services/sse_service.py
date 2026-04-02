import asyncio
import inspect
import json
from typing import AsyncGenerator

from sse_starlette.sse import ServerSentEvent


class SSEService:
    """Service for managing SSE streaming events for review sessions."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._queue: asyncio.Queue = asyncio.Queue()
        self._listeners = []

    async def event_generator(self) -> AsyncGenerator[ServerSentEvent, None]:
        """Generate SSE events for the client."""
        # Send initial connection event
        yield ServerSentEvent(
            event="connected",
            data=json.dumps({"session_id": self.session_id, "status": "connected"}),
        )

        # Keep connection alive and send events
        while True:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=30.0)
                yield ServerSentEvent(
                    event=event.get("type", "message"),
                    data=json.dumps(event.get("data", {})),
                )
            except asyncio.TimeoutError:
                # Send keep-alive comment
                yield ServerSentEvent(event="ping", data=json.dumps({}))
            except asyncio.CancelledError:
                break

    async def push_dimension_start(self, dimension: str):
        """Push a dimension review start event."""
        await self._publish("dimension_start", {"dimension": dimension, "status": "started"})

    async def push_dimension_complete(self, dimension: str, score: float, issues: list):
        """Push a dimension review complete event."""
        await self._publish("dimension_complete", {"dimension": dimension, "score": score, "issues": issues})

    async def push_streaming(self, content: str):
        """Push a streaming content event."""
        await self._publish("streaming", {"content": content})

    async def push_complete(self, report: dict):
        """Push the complete report event."""
        await self._publish("complete", report)

    async def push_error(self, message: str):
        """Push an error event."""
        await self._publish("error", {"message": message})

    def subscribe(self, listener):
        """Subscribe to emitted events for side effects such as session tracking."""
        self._listeners.append(listener)

    async def _publish(self, event_type: str, data: dict):
        await self._queue.put({
            "type": event_type,
            "data": data,
        })

        for listener in self._listeners:
            result = listener(event_type, data)
            if inspect.isawaitable(result):
                await result
