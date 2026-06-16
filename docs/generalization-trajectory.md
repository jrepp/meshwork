# Meshwork Generalization Trajectory

Meshwork is currently a Mythica automation runtime with a reusable distributed
job substrate inside it. The goal of this trajectory is to separate that
substrate into independently useful components while preserving the existing
Mythica workflows during the transition.

## Target Shape

Meshwork should become a small family of composable packages or optional
extras:

- `meshwork-core`: typed job contracts, worker registry, execution lifecycle,
  stream item models, generic parameter models, and protocol interfaces.
- `meshwork-transports`: NATS, HTTP/FastAPI, in-memory, and future transport
  implementations.
- `meshwork-storage`: file resolution, upload/download abstractions, and local
  filesystem implementations.
- `meshwork-auth`: generic identity/session/authorization protocols plus
  optional JWT helpers.
- `meshwork-houdini`: Houdini parameter/interface models and compilers.
- `meshwork-mythica`: Mythica routes, asset/job API publishing, roles, alerts,
  default automations, and compatibility shims.

This can start as modules and extras in one repository. It does not need to
become multiple distributions until the boundaries have stabilized.

## Design Principles

- Core models should not mention Mythica, Houdini, NATS, FastAPI, Discord, or a
  specific asset API.
- Product behavior should live behind adapters with narrow protocols.
- Existing Mythica behavior should keep working through compatibility imports
  and default adapter wiring.
- Transport and storage should be replaceable independently.
- Script execution should be explicitly opt-in and isolated from the default
  worker runtime.
- The public API should be deliberate: users should import from stable package
  entry points instead of deep internal modules.

## Long Session Objective Function

The long-session objective is to maximize Meshwork's reusable core value while
minimizing breakage to the existing Mythica automation runtime.

In practical terms:

```text
maximize:
  general_usefulness
  + boundary_clarity
  + compatibility_preservation
  + local_testability
  + dependency_optionality
  + documentation_completeness
  + security_explicitness

minimize:
  Mythica/Houdini/NATS/FastAPI coupling in core
  + required dependencies for basic use
  + undocumented public behavior
  + migration surprise
  + implicit script execution risk
```

A long session is complete when the following conditions are true:

1. **Core Independence**
   - `meshwork.core` can be imported without importing Mythica, Houdini, NATS,
     FastAPI, Discord, or OpenTelemetry-specific modules.
   - A minimal local automation can run with only core types plus in-memory
     adapters.
   - Core tests do not require network services, Mythica configuration, NATS, or
     FastAPI.

2. **Stable Public API**
   - New users can define a request model, response stream item, operation
     handler, worker, and local runner through documented public imports.
   - Existing deep imports either still work or emit intentional deprecation
     warnings with documented replacements.
   - `meshwork/__init__.py` and subpackage `__init__.py` files expose the
     intended API surface.

3. **Adapter Boundaries**
   - Worker execution depends on protocols for publishing, result storage, file
     resolution, and transport.
   - NATS, FastAPI, Mythica API calls, and Houdini interface generation are
     adapters or integrations, not core requirements.
   - In-memory implementations exist for tests and examples.

4. **Mythica Compatibility**
   - Current Mythica automation behavior still passes compatibility tests:
     catalog generation, script automations, job result publication, file
     uploads, event completion, and role checks.
   - Product-specific routes and defaults are wired by a Mythica factory or
     integration package, not by the generic worker constructor.

5. **Generic Parameters**
   - Generic parameter models can be used without Houdini imports.
   - Houdini parameter/template generation remains available through an explicit
     Houdini integration.
   - Existing Houdini behavior remains covered by tests.

6. **Packaging And Install Shape**
   - Basic installation has a small dependency set.
   - Optional extras or equivalent dependency groups exist for NATS, HTTP,
     telemetry, auth, Houdini, Mythica, and development tools.
   - Lockfiles and project metadata agree on the supported Python version.

7. **Script Execution Safety**
   - Script execution is disabled unless explicitly enabled.
   - Trusted and isolated execution modes are documented.
   - Any raw `exec` path is clearly marked as trusted-code-only.

8. **Documentation Completeness**
   - Docs explain what Meshwork is, what the core abstractions are, and how to
     use it without Mythica.
   - Docs include minimal local, NATS, HTTP/FastAPI, file IO, Houdini, and
     Mythica compatibility examples.
   - A migration guide maps old imports and concepts to new ones.

9. **Verification**
   - Python 3.14 tests pass.
   - Ruff passes.
   - Compile/conformance passes.
   - Mypy passes for the intended checked surface and remaining unchecked areas
     are explicitly scoped and tracked as type-debt.

The session should prefer small, reversible steps. If a change would break
Mythica compatibility or require broad handler rewrites, it should first add a
compatibility adapter or migration shim. If two paths provide similar
generality, prefer the one that reduces required dependencies and makes local
testing simpler.

## Proposed Boundaries

| Current Area | Future Home | Notes |
| --- | --- | --- |
| `meshwork.models.streaming` | `meshwork.core.streams` | Mostly reusable as-is. Remove product-specific stream variants or move them to integrations. |
| `meshwork.automation.models` | `meshwork.core.jobs` | Keep request/result/automation contracts; rename fields only after compatibility layer exists. |
| `meshwork.automation.worker` | `meshwork.core.worker` plus transport adapters | Worker should depend on protocols for publishing, resolving files, telemetry, and authorization. |
| `meshwork.automation.adapters` | `meshwork.transports.nats` and `meshwork.transports.http` | NATS subject scoping should be configurable, not Mythica environment/location-specific. |
| `meshwork.automation.publishers` | `meshwork.core.publisher` plus `meshwork.mythica.publisher` | Split stream publication from Mythica job/file API writes. |
| `meshwork.models.params` | `meshwork.core.params` and `meshwork.houdini.params` | Generic parameter specs should not return Houdini template specs by default. |
| `meshwork.compile.rpsc`, `meshwork.models.hou*` | `meshwork.houdini` | Treat Houdini as an integration. |
| `meshwork.auth.*` | `meshwork.mythica.auth` first, then generic auth protocols | Current roles and token audience are product-specific. |
| `meshwork.runtime.params` | `meshwork.storage.resolution` | File resolution should be driven by a `FileResolver` protocol. |
| `meshwork.runtime.alerts` | `meshwork.mythica.alerts` or `meshwork.observability.alerts` | Discord webhook is integration-specific. |
| `meshwork.automation.automations` | `meshwork.mythica.scripting` | Default `/mythica/script` automations should not load in core by default. |
| `meshwork.automation.workflow` | `meshwork.workflow.reactflow` plus `meshwork.mythica.workflow` | React Flow parsing can be generic; `mythicaFlow` handling is product-specific. |

## Phase 0: Baseline And Contract Capture

Objective: make the existing behavior observable before moving pieces.

- Keep the Python 3.14 environment green.
- Add a concise architecture document describing the current execution flow:
  request -> validation -> parameter resolution -> provider execution -> stream
  publication -> completion.
- Add examples for the current API:
  - local in-process automation
  - NATS automation
  - FastAPI automation
  - file output automation
- Snapshot current Mythica behavior with integration-style tests around:
  - catalog generation
  - `/mythica/script`
  - job result publishing
  - event completion processing
- Decide whether `poetry.lock` remains supported. If not, remove it in a
  dedicated cleanup change. If yes, regenerate it after the Python 3.14 move.

Exit criteria:

- Tests pass on Python 3.14.
- Examples run locally.
- Current Mythica behavior has explicit compatibility coverage.

## Phase 1: Public API And Naming

Objective: give future users stable entry points before deeper refactors.

- Populate `meshwork/__init__.py` with the intended public API.
- Add subpackage-level exports for:
  - `meshwork.core`
  - `meshwork.transports`
  - `meshwork.integrations`
- Mark deep imports as internal in docs.
- Add deprecation warnings only where imports are actively being moved.
- Rename user-facing concepts in docs from product terms to general terms:
  - automation -> job handler or operation
  - provider -> handler
  - result publisher -> stream publisher
  - path -> operation route

Exit criteria:

- A new project can define and run a simple Meshwork operation using only public
  imports.
- Existing imports still work.

## Phase 2: Protocol Extraction

Objective: stop the core worker from knowing about product infrastructure.

Introduce protocols:

```python
class StreamPublisher(Protocol):
    def publish(self, item: ProcessStreamItem, *, complete: bool = False) -> None: ...


class FileResolver(Protocol):
    def resolve(self, value: FileParameter, directory: str) -> FileParameter: ...


class ResultStore(Protocol):
    def record_result(self, request: AutomationRequest, item: ProcessStreamItem) -> None: ...
    def complete(self, request: AutomationRequest) -> None: ...


class Transport(Protocol):
    async def publish(self, subject: str, payload: dict) -> None: ...
    async def listen(self, subject: str, callback: Callable[[dict], Awaitable[None]]) -> None: ...
```

Then:

- Refactor `Worker` to receive dependencies rather than constructing
  `NatsAdapter`, `RestAdapter`, and `ResultPublisher` directly.
- Keep default construction equivalent to today through a compatibility factory.
- Move Mythica job/file endpoint writes into a `MythicaResultStore`.
- Move NATS subject scoping into configurable `SubjectScope`.

Exit criteria:

- Worker tests can run entirely with in-memory publisher/resolver/store objects.
- Mythica compatibility tests still pass with the Mythica adapter bundle.

## Phase 3: Generic Parameters First, Houdini As Integration

Objective: make typed parameter schemas useful outside Houdini.

- Split generic specs from Houdini parm template specs.
- Change `ParameterSet.get_parameter_specs()` to return generic specs.
- Add `HoudiniInterfaceBuilder.from_parameter_set(...)` for Houdini-specific
  interface generation.
- Keep a compatibility method such as
  `ParameterSet.get_houdini_parameter_specs()` during the migration.
- Move `houTypes`, `houClasses`, and RPSC compiler into `meshwork.houdini`.

Exit criteria:

- A non-Houdini project can use `ParameterSet` without importing Houdini models.
- Houdini tests still pass through the integration namespace.

## Phase 4: Transport And Runtime Adapters

Objective: make Meshwork useful in more deployment shapes.

Add first-class adapters:

- `InMemoryTransport` for tests, notebooks, local workflows, and examples.
- `NatsTransport` for distributed workers.
- `FastApiTransport` or `FastApiAppFactory` for HTTP execution.
- `LocalFileResolver` for filesystem-only workflows.
- `HttpFileResolver` for API-backed workflows.
- `NoopResultStore` for simple fire-and-return jobs.

Exit criteria:

- Documentation includes a minimal local example with no NATS, no FastAPI, and
  no Mythica API.
- NATS and FastAPI are optional extras rather than mandatory dependencies for
  core use.

## Phase 5: Mythica Compatibility Package

Objective: isolate the original product behavior without breaking it.

- Move `/mythica/...` routes into `meshwork.mythica`.
- Move Mythica auth roles and token audience into `meshwork.mythica.auth`.
- Move asset/job result upload behavior into `meshwork.mythica.publisher`.
- Move Discord infra alerts into `meshwork.mythica.alerts` or an observability
  integration.
- Provide `create_mythica_worker(...)` that wires the old defaults.

Exit criteria:

- Existing Mythica service code can migrate by changing construction/imports,
  not by rewriting job handlers.
- Core package tests do not require Mythica configuration.

## Phase 6: Script Execution Safety

Objective: turn script automation from an implicit default into a controlled
extension point.

- Remove script automations from the default core worker catalog.
- Add explicit `enable_script_automations(...)` wiring.
- Define security modes:
  - disabled
  - trusted local scripts
  - isolated subprocess
  - externally sandboxed execution
- Document that raw `exec` is trusted-code-only.
- Add limits for timeout, environment, imports, and filesystem access in any
  sandboxed mode.

Exit criteria:

- General users do not get `exec` behavior unless they explicitly request it.
- Mythica can preserve current scripting behavior through the Mythica bundle.

## Phase 7: Packaging And Dependency Slimming

Objective: reduce install weight and make adoption less surprising.

Suggested extras:

- `meshwork[nats]`: `nats-py`
- `meshwork[http]`: `fastapi`, `uvicorn`, `requests` or `aiohttp`
- `meshwork[telemetry]`: OpenTelemetry packages
- `meshwork[auth]`: `pyjwt`, `cryptography`, `base58`, `gcid`
- `meshwork[houdini]`: Houdini interface support
- `meshwork[mythica]`: Mythica API compatibility bundle
- `meshwork[dev]`: pytest, ruff, mypy, coverage

Exit criteria:

- `pip install meshwork` installs a small, useful core.
- Full Mythica behavior is available with an explicit extra.

## Phase 8: Documentation For General Use

Objective: make the library legible to users who do not know the original
project.

Create docs for:

- What Meshwork is and is not.
- Core concepts: operation, request, stream item, publisher, transport,
  resolver, result store.
- Minimal local example.
- Distributed NATS example.
- HTTP/FastAPI example.
- File inputs and outputs.
- Parameter schemas.
- Integrations: Houdini and Mythica.
- Migration guide from current imports to public imports.

Exit criteria:

- A new user can build a small non-Mythica automation from docs alone.
- Existing Mythica users have an explicit compatibility path.

## Suggested First Three Pull Requests

1. **Document current architecture and add examples**
   - Add current-flow docs.
   - Add local, NATS, and FastAPI examples.
   - Keep code changes minimal.

2. **Introduce protocols and dependency injection**
   - Add `StreamPublisher`, `FileResolver`, `ResultStore`, and `Transport`
     protocols.
   - Refactor `Worker` construction around injected dependencies.
   - Preserve old defaults with a compatibility factory.
   - Keep bare `Worker()` generic; wire product defaults in
     `create_mythica_worker()`.

3. **Split generic and Houdini parameter generation**
   - Add generic parameter spec generation.
   - Move Houdini-specific generation behind an integration function.
   - Keep compatibility methods for existing callers.

## Success Metrics

- A new project can use Meshwork without Mythica services.
- Core import graph has no Mythica, Houdini, NATS, FastAPI, Discord, or
  OpenTelemetry dependency.
- Existing Mythica automation tests still pass.
- Minimal core install has fewer dependencies than the current full stack.
- Public examples cover local, distributed, and HTTP execution.
- Script execution is disabled unless explicitly enabled.
