# Meshwork Architecture

Meshwork is being segmented into a reusable core plus optional integrations.
The existing Mythica automation runtime remains supported, but new projects
should start from the public namespaces described here.

For the cross-process wire contract, see `docs/protocol.md`.

## Core Flow

The generic execution flow is:

```text
request payload
  -> request model validation
  -> optional file/reference resolution
  -> operation handler execution
  -> stream item publication
  -> optional result storage/completion
```

The core concepts are:

- **ParameterSet**: typed operation input model.
- **ProcessStreamItem**: typed output or status item emitted by an operation.
- **Operation handler**: callable that accepts a request model and a publisher.
- **StreamPublisher**: protocol for publishing progress, messages, files, and
  final results.
- **Transport**: protocol for moving request payloads between processes.
- **FileResolver**: protocol for resolving file references into local paths.
- **ResultStore**: protocol for persisting results and completion state.

## Public Namespaces

- `meshwork.core`: generic contracts, local runner, protocols, parameter models,
  and stream models.
- `meshwork.transports`: transport adapters such as NATS, REST compatibility,
  and in-memory transport.
- `meshwork.storage`: file resolution helpers.
- `meshwork.houdini`: Houdini-specific parameter/interface integration.
- `meshwork.mythica`: Mythica compatibility layer.

Existing modules such as `meshwork.automation`, `meshwork.models`, `meshwork.auth`,
and `meshwork.runtime` remain available for compatibility. They should be treated
as legacy import paths for new work.

## Dependency Direction

The desired dependency direction is:

```text
meshwork.core
  <- meshwork.transports
  <- meshwork.storage
  <- meshwork.houdini
  <- meshwork.mythica
```

Core should not depend on Mythica, Houdini, NATS, FastAPI, Discord, or a
specific API backend. Integrations may depend on core.

## Local Execution

For tests, examples, notebooks, and simple services, use `LocalRunner`.

```python
from meshwork.core import LocalRunner, Message, ParameterSet


class EchoRequest(ParameterSet):
    message: str


def echo(request: EchoRequest, publisher: LocalRunner) -> Message:
    return Message(message=request.message)


runner = LocalRunner()
result = runner.run(echo, EchoRequest(message="hello"))
assert result.result.message == "hello"
```

## Mythica Compatibility

The current Mythica runtime is preserved through `meshwork.mythica`.

```python
from meshwork.mythica import create_mythica_worker


worker = create_mythica_worker()
```

This factory wires the same default behavior as the current `Worker`, including
the `/mythica/automations` catalog and script automation routes.

The underlying compatibility worker also accepts injected NATS and REST adapters
plus runtime hooks for API base URI lookup, headers, parameter resolution,
alerting, publisher construction, and event result processing. Bare `Worker()`
is intentionally generic and does not register Mythica defaults unless the
application layer supplies them.

## Segmentation Status

The current implementation has established the new public namespaces and a
generic `meshwork.core` API. Existing implementation modules still power much of
the compatibility layer. Future work should move internals behind the new
protocols without changing the public imports.
