# Mythica Migration Guide

This guide describes how Mythica application layers should move from the
original Meshwork internals to the segmented library.

The goal is a clean port, not a rewrite. Existing job handlers should continue
to work while construction, imports, and product-specific defaults move into
the Mythica compatibility layer.

## Migration Strategy

1. Update imports to public namespaces.
2. Replace direct worker construction with the Mythica factory.
3. Keep existing automation handlers unchanged.
4. Move new non-product code to `meshwork.core`.
5. Move product-specific API behavior to `meshwork.mythica`.
6. Add compatibility tests around each migrated service.

## Import Map

| Old Import | New Import | Notes |
| --- | --- | --- |
| `meshwork.automation.worker.Worker` | `meshwork.mythica.create_mythica_worker` | Use the factory for current Mythica defaults. |
| `meshwork.automation.models.AutomationRequest` | `meshwork.core.AutomationRequest` for new generic code | Existing Mythica code may keep old imports until handlers are ported. |
| `meshwork.automation.models.AutomationModel` | `meshwork.core.AutomationModel` for generic operations | The old model remains compatible with Mythica worker internals. |
| `meshwork.models.streaming.Message` | `meshwork.core.Message` | Use core stream items for new handlers. |
| `meshwork.models.streaming.Progress` | `meshwork.core.Progress` | Same conceptual model, generic import. |
| `meshwork.models.params.ParameterSet` | `meshwork.core.ParameterSet` for generic handlers | Use `meshwork.houdini` when Houdini interface specs are needed. |
| `meshwork.automation.adapters.NatsAdapter` | `meshwork.transports.NatsAdapter` | Compatibility export. |
| `meshwork.automation.adapters.RestAdapter` | `meshwork.transports.RestAdapter` | Compatibility export. |
| `meshwork.runtime.params.resolve_params` | `meshwork.storage.resolve_params` | Compatibility export. |
| `meshwork.compile.rpsc.compile_interface` | `meshwork.houdini.compile_interface` | Houdini-specific. |
| `meshwork.models.houTypes` / `houClasses` | `meshwork.houdini` | Keep Houdini code out of generic layers. |
| `meshwork.auth.*` | `meshwork.mythica.auth` | Current roles/token audience are Mythica-specific. |
| `meshwork.automation.publishers.ResultPublisher` | `meshwork.mythica.publisher.ResultPublisher` | Publishes to Mythica job/file APIs. |
| `meshwork.automation.automations.*` | `meshwork.mythica.scripting.*` | Script automation remains a Mythica compatibility feature. |

## Worker Construction

Before:

```python
from meshwork.automation.worker import Worker


worker = Worker()
worker.start(subject, automations)
```

After:

```python
from meshwork.mythica import create_mythica_worker


worker = create_mythica_worker()
worker.start(subject, automations)
```

This preserves the current catalog and script automation defaults while making
the product dependency explicit.

Important: bare `Worker()` is now the composable Meshwork constructor. It does
not register `/mythica/...` defaults by itself. Mythica application layers should
use `create_mythica_worker()` until they are ready to supply their own
composition.

For services that already construct custom test doubles, the compatibility
worker now accepts injected adapters:

```python
from meshwork.mythica.worker import Worker


worker = Worker(nats=my_nats_adapter, rest=my_rest_adapter)
```

Runtime hooks can also be injected:

```python
worker = Worker(
    nats=my_nats_adapter,
    rest=my_rest_adapter,
    api_base_uri_provider=my_api_base_uri,
    headers_provider=my_headers,
    param_resolver=my_param_resolver,
    alert_handler=my_alert_handler,
    process_event_results=True,
)
```

Use this as the bridge while moving service tests toward in-memory core adapters
and moving Mythica-specific implementation details into the application
composition layer.

## Handler Porting

Current Mythica handlers can continue to use the existing old models until their
service is migrated. New generic handlers should use core imports:

```python
from meshwork.core import Message, ParameterSet, Progress


class ThumbnailRequest(ParameterSet):
    source_file: str


def make_thumbnail(request: ThumbnailRequest, publisher) -> Message:
    publisher.publish(Progress(progress=25))
    return Message(message=f"processed {request.source_file}")
```

If the handler needs Houdini-generated UI metadata, keep that dependency
explicit:

```python
from meshwork.houdini.params import FloatParmTemplateSpec
```

## Result Publishing

Mythica job result APIs, file uploads, asset content updates, and event
completion are product-layer behavior. Keep those behind:

```python
from meshwork.mythica.publisher import ResultPublisher
```

Generic projects should use a core `StreamPublisher` implementation, such as
`LocalRunner`, or provide their own `ResultStore`.

## Script Automations

Script automation is trusted-code execution and should not be enabled
implicitly in generic services.

For Mythica compatibility:

```python
from meshwork.mythica.scripting import get_default_automations
```

For generic services, prefer explicit operation registration. If script
execution is needed, add it deliberately and document the trust boundary.

## Service Migration Checklist

- Replace `Worker()` construction with `create_mythica_worker()`.
- Move auth imports to `meshwork.mythica.auth`.
- Move result publisher imports to `meshwork.mythica.publisher`.
- Move script automation imports to `meshwork.mythica.scripting`.
- Move Houdini imports to `meshwork.houdini`.
- Use `meshwork.core` imports for new generic request/response models.
- Add a service-level test that confirms the expected automation paths are
  registered.
- Run Python 3.14 tests for the service.

## Compatibility Rule

Do not rewrite working Mythica handlers just to adopt new imports. First migrate
construction and product-layer imports. Then move individual handlers to
`meshwork.core` when they are being touched for feature work.
