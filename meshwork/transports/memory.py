"""In-memory transport for tests and local examples."""

from collections import defaultdict
from collections.abc import Awaitable, Callable

from meshwork.core.protocols import Payload

MessageCallback = Callable[[Payload], Awaitable[None]]


class InMemoryTransport:
    """A simple async transport that stores messages in memory."""

    def __init__(self) -> None:
        self.messages: dict[str, list[Payload]] = defaultdict(list)
        self.listeners: dict[str, list[MessageCallback]] = defaultdict(list)

    async def publish(self, subject: str, payload: Payload) -> None:
        self.messages[subject].append(payload)
        for callback in self.listeners[subject]:
            await callback(payload)

    async def listen(self, subject: str, callback: MessageCallback) -> None:
        self.listeners[subject].append(callback)
