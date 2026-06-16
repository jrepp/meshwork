# Meshwork Protocol Specification

Status: draft

Protocol version: `meshwork.v0.1`

This document defines the interoperable contracts for Meshwork clients,
workers, transports, and result consumers. It is intentionally narrower than
the full Python API: it describes the data and message behavior that must remain
stable across implementations.

## Goals

The Meshwork protocol exists to let independent processes:

- describe typed automation operations,
- submit operation requests,
- publish progress and results,
- resolve file references when an application supplies a resolver,
- authenticate application-specific requests, and
- exchange messages over a replaceable transport.

The reusable protocol must not require Mythica, Houdini, FastAPI, NATS, or any
specific storage backend. Those systems are integrations layered on top of the
core protocol.

## Terminology

- **Client**: process that submits an automation request.
- **Worker**: process that validates and executes an automation request.
- **Operation**: callable registered at a path, with typed input and output.
- **Transport**: mechanism used to publish request/result payloads.
- **Result consumer**: process or API that receives stream items.
- **Application layer**: product-specific code that supplies auth policy,
  storage, HTTP APIs, subject naming, and worker composition.

The terms MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are used with their usual
normative meanings.

## Versioning

Every serialized protocol envelope SHOULD include a `protocol` string. When it
is omitted, implementations MAY treat the payload as `meshwork.v0.1` for
compatibility with current Meshwork models.

Compatible v0.1 changes may add optional fields. Removing fields, changing field
meaning, or changing required field types requires a new protocol version.

## Encoding

Protocol messages MUST be encoded as JSON-compatible objects unless a transport
explicitly defines a different binary envelope. Field names use the Python model
names as wire names.

Implementations SHOULD ignore unknown fields at the envelope level and SHOULD
preserve unknown application fields inside request `data`.

## Operation Description

An operation is described by the `AutomationModel` contract:

```json
{
  "path": "/example/echo",
  "inputModel": "EchoRequest",
  "outputModel": "Message",
  "hidden": false
}
```

The Python model also carries `provider` and optional `interfaceModel` callables.
Those are in-process registration details and MUST NOT be required by non-Python
wire implementations.

Operation paths MUST be stable strings. Applications SHOULD use slash-prefixed
paths for routable operations, for example `/image/thumbnail`.

## Request Message

The canonical request payload is `AutomationRequest`.

```json
{
  "protocol": "meshwork.v0.1",
  "process_guid": "process-123",
  "correlation": "request-456",
  "results_subject": "client-789",
  "job_id": "job-abc",
  "auth_token": "opaque-token",
  "path": "/example/echo",
  "data": {
    "message": "hello"
  },
  "telemetry_context": {},
  "event_id": null
}
```

Required fields:

- `process_guid`: stable identifier for the execution process.
- `correlation`: stable identifier used to correlate request and stream items.
- `path`: operation path to execute.
- `data`: JSON object used to construct the operation input model.

Optional fields:

- `results_subject`: application transport subject for asynchronous results.
- `job_id`: application persistence identifier.
- `auth_token`: opaque application auth credential.
- `telemetry_context`: application telemetry context object.
- `event_id`: application event identifier.

Workers MUST validate `data` against the registered input model before invoking
the operation. Workers SHOULD publish an `Error` stream item when validation or
execution fails.

## Bulk Request Message

Bulk execution uses `BulkAutomationRequest`.

```json
{
  "protocol": "meshwork.v0.1",
  "is_bulk_processing": true,
  "requests": [],
  "event_id": "event-123",
  "telemetry_context": {}
}
```

`requests` MUST contain `AutomationRequest` objects. Workers MAY process bulk
requests sequentially or concurrently, but each emitted stream item MUST retain
the request correlation.

## Parameter Data

Operation input models inherit from `ParameterSet`. Valid parameter values are:

- integer,
- float,
- string,
- boolean,
- `FileParameter`,
- lists/tuples/sets containing valid parameter values,
- dictionaries containing valid parameter values.

`FileParameter` is:

```json
{
  "file_id": "file-123",
  "file_path": null
}
```

`file_id` identifies an external application file. `file_path` identifies a
local resolved file path and SHOULD be supplied only after a trusted resolver has
materialized the file for a worker.

## Parameter Interface Metadata

Generic parameter interface metadata is represented by `ParameterSpec`.

```json
{
  "params": {
    "message": {
      "param_type": "string",
      "label": "message",
      "default": ""
    }
  },
  "default": {
    "message": "hello"
  },
  "hidden": {}
}
```

Supported `param_type` values in the generic protocol are:

- `int`
- `float`
- `string`
- `bool`
- `enum`
- `file`
- `ramp`

Houdini-specific templates are not part of the core wire protocol. Applications
that need Houdini UI metadata SHOULD expose it through `meshwork.houdini` or an
application-specific extension field.

## Stream Items

Operation output and status messages are `ProcessStreamItem` objects. Every
stream item has:

- `item_type`: discriminator string,
- `correlation`: request correlation,
- `process_guid`: execution process identifier,
- `job_id`: optional application job identifier,
- `index`: optional application ordering/index field.

Workers MUST set `correlation` to the originating request correlation for every
stream item. Workers SHOULD set `process_guid` and `job_id` when those values are
available.

### Progress

```json
{
  "item_type": "progress",
  "correlation": "request-456",
  "process_guid": "process-123",
  "job_id": "job-abc",
  "progress": 50
}
```

`progress` SHOULD be an integer from 0 to 100.

### Message

```json
{
  "item_type": "message",
  "correlation": "request-456",
  "process_guid": "process-123",
  "job_id": "job-abc",
  "message": "done"
}
```

### Error

```json
{
  "item_type": "error",
  "correlation": "request-456",
  "process_guid": "process-123",
  "job_id": "job-abc",
  "error": "validation failed"
}
```

Errors SHOULD be safe to display to an operator. Sensitive exception details
SHOULD remain in application logs.

### Output Files

```json
{
  "item_type": "file",
  "correlation": "request-456",
  "process_guid": "process-123",
  "job_id": "job-abc",
  "files": {
    "preview": ["file-456"]
  }
}
```

Values in `files` SHOULD be application file identifiers after upload or storage
registration. Local file paths MUST NOT be sent to untrusted consumers unless the
application explicitly defines that behavior.

### File Content Chunk

```json
{
  "item_type": "file_content_chunk",
  "correlation": "request-456",
  "process_guid": "process-123",
  "job_id": "job-abc",
  "file_key": "preview",
  "file_index": 0,
  "chunk_index": 0,
  "total_chunks": 3,
  "file_size": 131072,
  "encoded_data": "base64..."
}
```

`encoded_data` MUST be base64 text. Consumers MUST reassemble chunks by
`correlation`, `file_key`, `file_index`, and `chunk_index`.

### Job Definition

```json
{
  "item_type": "job_def",
  "correlation": "request-456",
  "process_guid": "process-123",
  "job_id": "job-abc",
  "job_def_id": "",
  "job_type": "example",
  "name": "Example",
  "description": "Example operation",
  "parameter_spec": {},
  "owner_id": null,
  "source": null
}
```

This item is retained for compatibility with the current application layer.
Generic projects MAY ignore it.

## Transport Contract

A Meshwork transport implements:

```python
async def publish(subject: str, payload: dict) -> None: ...
async def listen(subject: str, callback) -> None: ...
```

Transport implementations MUST deliver JSON-compatible payload dictionaries to
callbacks. They SHOULD preserve message ordering per subject when the underlying
transport supports it.

Transports SHOULD NOT interpret `auth_token`, `data`, or stream item bodies.
Validation belongs to workers and application layers.

## NATS Binding

The compatibility NATS binding scopes logical subjects with environment and
location:

```text
{subject}.{environment}.{location}
{subject}.{environment}.{location}.{entity}
```

For example:

```text
result.debug.dev-machine.client-123
```

`NatsAdapter.publish(subject, payload)` publishes to the environment/location
scoped subject. `NatsAdapter.publish_to(subject, entity, payload)` publishes to
the entity-scoped subject.

Current compatibility aliases are:

- `post(subject, data)` equals `publish(subject, data)`.
- `post_to(subject, entity, data)` equals `publish_to(subject, entity, data)`.
- `listen_as(subject, entity, callback)` listens on an entity-scoped subject.
- `stop_listening(subject, entity=None)` unsubscribes using logical subject
  inputs.
- `unlisten(scoped_subject)` unsubscribes using a fully scoped subject.

New code SHOULD prefer `publish`, `publish_to`, `listen`, `listen_as`, and
`stop_listening`.

## Authentication

The core protocol treats `auth_token` as opaque. Application layers MAY define
token formats and role semantics.

The current Mythica compatibility layer uses HS256 JWTs with audience
`mythica_auth_token` and these claims:

- `profile_id`
- `email`
- `email_vs`
- `location`
- `roles`
- `env`
- `aud`
- `mpr`

Generic Meshwork workers MUST NOT require Mythica JWTs. Mythica application
workers SHOULD decode tokens through `meshwork.auth` or `meshwork.mythica.auth`
and apply `validate_roles` at the application boundary.

## Execution Semantics

For a single request, a worker SHOULD:

1. Receive an `AutomationRequest`.
2. Validate `path` against the registered operation catalog.
3. Validate `data` against the operation input model.
4. Resolve `FileParameter` values if a `FileResolver` is configured.
5. Execute the operation.
6. Publish zero or more progress/status stream items.
7. Publish one final output stream item.
8. Record completion if a `ResultStore` is configured.

If execution fails, the worker SHOULD publish an `Error` item and SHOULD mark
the request processed according to application policy.

## Extension Points

Implementations MAY add application-specific fields if they do not change the
meaning of standard fields. Recommended extension points are:

- top-level `protocol` envelope metadata,
- `telemetry_context`,
- operation-specific `data`,
- application-specific stream item subclasses,
- application-specific parameter spec fields.

Extensions that cross process boundaries SHOULD be documented by the
application layer.

## Compatibility Notes

The current Python package still contains legacy modules under
`meshwork.automation`, `meshwork.models`, and `meshwork.runtime`. New generic
code SHOULD import from:

- `meshwork`
- `meshwork.core`
- `meshwork.transports`
- `meshwork.storage`

Mythica application code SHOULD import product-specific behavior from:

- `meshwork.mythica`
- `meshwork.mythica.auth`
- `meshwork.mythica.publisher`
- `meshwork.mythica.scripting`

The protocol spec should be updated whenever a new public wire field or
transport semantic is introduced.
