"""Core job contracts without product-specific dependencies."""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from meshwork.core.params import ParameterSet
from meshwork.core.streams import ProcessStreamItem


class AutomationModel(BaseModel):
    path: str
    provider: Callable
    inputModel: type[ParameterSet]
    outputModel: type[ProcessStreamItem]
    interfaceModel: Callable[[], list[Any]] | None = None
    hidden: bool = False

    @property
    def input_model(self) -> type[ParameterSet]:
        """Snake-case alias for new code."""

        return self.inputModel

    @property
    def output_model(self) -> type[ProcessStreamItem]:
        """Snake-case alias for new code."""

        return self.outputModel

    @property
    def interface_model(self) -> Callable[[], list[Any]] | None:
        """Snake-case alias for new code."""

        return self.interfaceModel


class AutomationRequest(BaseModel):
    process_guid: str = Field(default_factory=lambda: str(uuid4()))
    correlation: str = Field(default_factory=lambda: str(uuid4()))
    results_subject: str | None = None
    job_id: str | None = None
    auth_token: str | None = None
    path: str
    data: dict[str, Any] = Field(default_factory=dict)
    telemetry_context: dict | None = Field(default_factory=dict)
    event_id: str | None = None

    @classmethod
    def from_params(
        cls,
        path: str,
        params: ParameterSet | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> "AutomationRequest":
        """Create a request from a typed ParameterSet or plain dict."""

        data = params.model_dump() if isinstance(params, ParameterSet) else params
        return cls(path=path, data=data or {}, **kwargs)


class BulkAutomationRequest(BaseModel):
    is_bulk_processing: bool = True
    requests: list[AutomationRequest] = Field(default_factory=list)
    event_id: str | None = None
    telemetry_context: dict | None = Field(default_factory=dict)


class AutomationRequestResult(BaseModel):
    processed: bool = False
    request: AutomationRequest | None = None
    result: dict[str, Any] | None = None


class EventAutomationResponse(BaseModel):
    is_bulk_processing: bool = False
    processed: bool = False
    request_result: list[AutomationRequestResult] = Field(default_factory=list)


class AutomationsResponse(ProcessStreamItem):
    item_type: str = "automationsResponse"
    automations: dict[str, dict[str, Any]] = Field(default_factory=dict)


def operation(
    path: str,
    provider: Callable,
    input_model: type[ParameterSet],
    output_model: type[ProcessStreamItem],
    *,
    interface_model: Callable[[], list[Any]] | None = None,
    hidden: bool = False,
) -> AutomationModel:
    """Create an AutomationModel using snake-case arguments."""

    return AutomationModel(
        path=path,
        provider=provider,
        inputModel=input_model,
        outputModel=output_model,
        interfaceModel=interface_model,
        hidden=hidden,
    )


__all__ = [
    "AutomationModel",
    "AutomationRequest",
    "AutomationRequestResult",
    "AutomationsResponse",
    "BulkAutomationRequest",
    "EventAutomationResponse",
    "operation",
]
