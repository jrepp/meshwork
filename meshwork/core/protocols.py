"""Protocols that decouple Meshwork core execution from integrations."""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeAlias

from meshwork.core.jobs import AutomationRequest
from meshwork.core.params import FileParameter
from meshwork.core.streams import ProcessStreamItem

Payload: TypeAlias = dict[str, Any]


class StreamPublisher(Protocol):
    """Publishes process stream items from an operation."""

    def publish(self, item: ProcessStreamItem, *, complete: bool = False) -> None:
        """Publish a stream item."""


class FileResolver(Protocol):
    """Resolves external file references into local file paths."""

    def resolve(self, value: FileParameter, directory: str) -> FileParameter:
        """Resolve a file parameter into a local file."""


class ResultStore(Protocol):
    """Persists operation results and completion state."""

    def record_result(
        self, request: AutomationRequest, item: ProcessStreamItem
    ) -> None:
        """Record an emitted result."""

    def complete(self, request: AutomationRequest) -> None:
        """Mark a request complete."""


class Transport(Protocol):
    """Message transport used to publish and listen for job payloads."""

    async def publish(self, subject: str, payload: Payload) -> None:
        """Publish a payload."""

    async def listen(
        self, subject: str, callback: Callable[[Payload], Awaitable[None]]
    ) -> None:
        """Listen for payloads on a subject."""
