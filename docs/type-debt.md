# Type Checking Scope

Meshwork's new reusable surface is type checked first. The legacy Mythica,
Houdini, automation, and runtime modules predate the segmentation work and have
substantial existing type debt.

## Checked Surface

The `typecheck` script currently checks:

```text
meshwork/core
meshwork/transports/memory.py
tests/test_public_api.py
```

This surface covers the new generic public API, the protocol definitions, the
local runner, generic parameter models, generic stream models, and the in-memory
transport used by docs and examples.

The same scoped typecheck runs in the pre-commit hook. Expand this list whenever
legacy code is moved behind the segmented public API.

## Legacy Type Debt

Running `mypy .` currently reports hundreds of issues across legacy modules and
tests. The main categories are:

- missing annotations in older modules and tests
- untyped third-party dependency imports such as `gcid`
- Pydantic model unions that include both generic and Houdini-specific variants
- optional values that are used as concrete dicts/models
- legacy Houdini class wrappers with broad dynamic attributes

These are not new Python 3.14 runtime failures. They should be paid down module
by module as implementation moves behind the new public namespaces.

## Expansion Rule

When a legacy module is ported into the segmented architecture, add it to the
checked surface in the same change. New modules should not be added outside the
checked surface unless they are explicitly marked as compatibility shims.
