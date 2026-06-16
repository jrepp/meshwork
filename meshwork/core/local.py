"""Local execution helpers for dependency-light Meshwork usage."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from meshwork.core.params import ParameterSet
from meshwork.core.protocols import StreamPublisher
from meshwork.core.streams import ProcessStreamItem

RequestT = TypeVar("RequestT", bound=ParameterSet)
ResultT = TypeVar("ResultT", bound=ProcessStreamItem)


@dataclass
class LocalExecutionResult(Generic[ResultT]):
    """Result of a local operation run."""

    result: ResultT
    stream: list[ProcessStreamItem] = field(default_factory=list)


class LocalRunner(StreamPublisher):
    """Run a Meshwork operation in-process.

    This is intentionally small: it gives tests, examples, and simple projects a
    way to use Meshwork contracts without NATS, FastAPI, or the Mythica API.
    """

    def __init__(self) -> None:
        self.stream: list[ProcessStreamItem] = []

    def publish(self, item: ProcessStreamItem, *, complete: bool = False) -> None:
        self.stream.append(item)

    def result(self, item: ProcessStreamItem, complete: bool = False) -> None:
        """Compatibility alias for handlers that expect a ResultPublisher."""

        self.publish(item, complete=complete)

    def run(
        self,
        handler: Callable[[RequestT, StreamPublisher], ResultT],
        request: RequestT,
    ) -> LocalExecutionResult[ResultT]:
        self.stream = []
        result = handler(request, self)
        self.publish(result, complete=True)
        return LocalExecutionResult(result=result, stream=list(self.stream))


def run_local(
    handler: Callable[[RequestT, StreamPublisher], ResultT],
    request: RequestT,
) -> LocalExecutionResult[ResultT]:
    """Run one operation locally without manually constructing a runner."""

    return LocalRunner().run(handler, request)
