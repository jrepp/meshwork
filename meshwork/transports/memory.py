"""In-memory transport for tests and local examples."""

from collections import defaultdict
from collections.abc import Awaitable, Callable


class InMemoryTransport:
    """A simple async transport that stores messages in memory."""

    def __init__(self) -> None:
        self.messages: dict[str, list[dict]] = defaultdict(list)
        self.listeners: dict[str, list[Callable[[dict], Awaitable[None]]]] = (
            defaultdict(list)
        )

    async def publish(self, subject: str, payload: dict) -> None:
        self.messages[subject].append(payload)
        for callback in self.listeners[subject]:
            await callback(payload)

    async def listen(
        self, subject: str, callback: Callable[[dict], Awaitable[None]]
    ) -> None:
        self.listeners[subject].append(callback)
