import subprocess
import sys
from typing import Any, cast

from meshwork import (
    Error,
    Event,
    FileContentChunk,
    IntParameterSpec,
    JobDefinition,
    LocalRunner,
    Message,
    ParameterSet,
    ParameterSpec,
    StreamPublisher,
    StringParameterSpec,
    Transport,
    operation,
    run_local,
)
from meshwork.auth import decode_token, generate_token
from meshwork.core import AutomationModel, AutomationRequest, FileParameter, Progress
from meshwork.mythica import create_mythica_worker
from meshwork.mythica.worker import Worker
from meshwork.transports.memory import InMemoryTransport


class EchoRequest(ParameterSet):
    message: str


class DefaultedRequest(ParameterSet):
    message: str = "hello"
    count: int = 1


def echo_handler(request: EchoRequest, publisher: StreamPublisher) -> Message:
    publisher.publish(Progress(progress=50))
    return Message(message=request.message)


def test_core_public_api_local_runner() -> None:
    runner = LocalRunner()
    result = runner.run(echo_handler, EchoRequest(message="hello"))

    assert isinstance(result.result, Message)
    assert result.result.message == "hello"
    assert [item.item_type for item in result.stream] == ["progress", "message"]


def test_run_local_convenience() -> None:
    result = run_local(echo_handler, EchoRequest(message="hello"))

    assert result.result.message == "hello"
    assert [item.item_type for item in result.stream] == ["progress", "message"]


def test_local_runner_runs_are_isolated() -> None:
    runner = LocalRunner()

    first = runner.run(echo_handler, EchoRequest(message="first"))
    second = runner.run(echo_handler, EchoRequest(message="second"))

    assert [item.item_type for item in first.stream] == ["progress", "message"]
    assert [item.item_type for item in second.stream] == ["progress", "message"]
    assert second.result.message == "second"


def test_core_models_are_generic() -> None:
    request = AutomationRequest(
        process_guid="process",
        correlation="correlation",
        path="/echo",
        data={"message": "hello"},
    )
    file_param = FileParameter(file_id="file_123")

    assert request.path == "/echo"
    assert file_param.file_path is None


def test_automation_request_has_sensible_defaults() -> None:
    request = AutomationRequest(path="/echo")

    assert request.path == "/echo"
    assert request.data == {}
    assert request.process_guid
    assert request.correlation
    assert request.process_guid != request.correlation


def test_automation_request_from_params() -> None:
    request = AutomationRequest.from_params(
        "/echo",
        EchoRequest(message="hello"),
        results_subject="client",
    )

    assert request.path == "/echo"
    assert request.data == {"message": "hello"}
    assert request.results_subject == "client"


def test_stream_items_have_sensible_defaults() -> None:
    assert Progress().progress == 0
    assert Message().message == ""
    assert Error().error == ""


def test_automation_model_has_snake_case_accessors() -> None:
    model = AutomationModel(
        path="/echo",
        provider=echo_handler,
        inputModel=EchoRequest,
        outputModel=Message,
    )

    assert model.input_model is EchoRequest
    assert model.output_model is Message
    assert model.interface_model is None
    assert model.inputModel is model.input_model


def test_operation_factory_uses_snake_case_arguments() -> None:
    model = operation(
        "/echo",
        echo_handler,
        input_model=EchoRequest,
        output_model=Message,
        hidden=True,
    )

    assert model.path == "/echo"
    assert model.input_model is EchoRequest
    assert model.output_model is Message
    assert model.hidden is True


def test_parameter_set_named_parameter_spec() -> None:
    spec = EchoRequest.parameter_spec()

    assert isinstance(spec, ParameterSpec)
    assert isinstance(spec.params["message"], StringParameterSpec)
    assert spec.default is None


def test_parameter_set_uses_constructible_defaults() -> None:
    spec = DefaultedRequest.parameter_spec()

    assert isinstance(spec.params["message"], StringParameterSpec)
    assert isinstance(spec.params["count"], IntParameterSpec)
    assert spec.default == DefaultedRequest()


def test_root_exports_complete_core_models() -> None:
    assert Event is not None
    assert FileContentChunk is not None
    assert IntParameterSpec is not None
    assert JobDefinition is not None


def test_root_exports_core_protocols() -> None:
    assert StreamPublisher is not None
    assert Transport is not None


def test_auth_package_exports_token_helpers() -> None:
    token = generate_token(
        "prf_3mnLwbhLTFi7ngrFd9BYHUJb1spr",
        "api@test.local",
        2,
        "local-test",
        "test",
    )

    assert decode_token(token).email == "api@test.local"


def test_core_import_does_not_load_integration_modules() -> None:
    script = """
import sys
import meshwork.core
blocked = [
    "meshwork.models.houTypes",
    "meshwork.automation.worker",
    "nats",
    "fastapi",
]
loaded = [name for name in blocked if name in sys.modules]
if loaded:
    raise SystemExit(f"unexpected integration imports: {loaded}")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_in_memory_transport() -> None:
    seen: list[dict] = []
    transport = InMemoryTransport()

    async def callback(payload: dict) -> None:
        seen.append(payload)

    async def run() -> None:
        await transport.listen("jobs", callback)
        await transport.publish("jobs", {"id": "1"})

    import asyncio

    asyncio.run(run())

    assert transport.messages["jobs"] == [{"id": "1"}]
    assert seen == [{"id": "1"}]


def test_mythica_worker_factory_preserves_default_catalog() -> None:
    worker = create_mythica_worker()

    assert "/mythica/automations" in worker.automations
    assert "/mythica/script" in worker.automations


def test_generic_worker_has_no_mythica_defaults() -> None:
    worker = Worker()

    assert worker.automations == {}


def test_worker_accepts_injected_adapters() -> None:
    nats = cast(Any, object())
    rest = cast(Any, object())

    worker = Worker(nats=nats, rest=rest)

    assert worker.nats is nats
    assert worker.rest is rest


def test_worker_accepts_injected_runtime_hooks() -> None:
    calls = []

    def api_base_uri_provider() -> str:
        return "https://api.example.test/v1"

    def headers_provider() -> dict:
        return {"traceparent": "trace"}

    def param_resolver(
        endpoint: str, directory: str, params: ParameterSet, headers: dict
    ) -> None:
        calls.append((endpoint, directory, params, headers))

    worker = Worker(
        api_base_uri_provider=api_base_uri_provider,
        headers_provider=headers_provider,
        param_resolver=param_resolver,
    )

    assert worker.api_base_uri_provider() == "https://api.example.test/v1"
    assert worker.headers_provider() == {"traceparent": "trace"}
    assert worker.param_resolver is not None
    worker.param_resolver("endpoint", "directory", ParameterSet(), headers={})

    assert calls
