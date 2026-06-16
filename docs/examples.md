# Meshwork Examples

## Minimal Local Operation

```python
from meshwork import Message, ParameterSet, Progress, StreamPublisher, run_local


class EchoRequest(ParameterSet):
    message: str


def echo(request: EchoRequest, publisher: StreamPublisher) -> Message:
    publisher.publish(Progress(progress=50))
    return Message(message=request.message)


result = run_local(echo, EchoRequest(message="hello"))
print(result.result.message)
```

## In-Memory Transport

```python
import asyncio

from meshwork.transports.memory import InMemoryTransport


transport = InMemoryTransport()
seen = []


async def callback(payload: dict) -> None:
    seen.append(payload)


async def main() -> None:
    await transport.listen("jobs", callback)
    await transport.publish("jobs", {"id": "job_1"})


asyncio.run(main())
assert seen == [{"id": "job_1"}]
```

## Request Defaults

```python
from meshwork import AutomationRequest, Message, ParameterSet, operation


class EchoRequest(ParameterSet):
    message: str


def echo(request, publisher):
    return Message(message=request.message)


request = AutomationRequest(path="/echo")
assert request.data == {}
assert request.correlation

typed_request = AutomationRequest.from_params("/echo", EchoRequest(message="hello"))
echo_operation = operation("/echo", echo, EchoRequest, Message)
```

## NATS Compatibility

```python
from meshwork.transports import NatsAdapter


nats = NatsAdapter()
```

The NATS adapter currently preserves the existing Mythica-compatible subject
scoping. Future transport work should make scoping configurable.

## FastAPI/Mythica Worker Compatibility

```python
from meshwork.mythica import create_mythica_worker


worker = create_mythica_worker()
app = worker.start_web([])
```

## File Resolution

```python
from meshwork.core import FileParameter
from meshwork.storage import HttpFileResolver


resolver = HttpFileResolver("https://api.example.test/v1")
resolved = resolver.resolve(FileParameter(file_id="file_123"), "/tmp")
print(resolved.file_path)
```

## Houdini Interface Compilation

```python
from meshwork.houdini import compile_interface


spec = compile_interface(
    """
    {
      "defaults": {},
      "inputLabels": ["Input"]
    }
    """
)
```
