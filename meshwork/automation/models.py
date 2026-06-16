from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

from meshwork.models.params import (
    FileParameter,
    HoudiniParmTemplateSpecType,
    IntParameterSpec,
    ParameterSet,
)
from meshwork.models.streaming import ProcessStreamItem


class AutomationsResponse(ProcessStreamItem):
    item_type: Literal["automationsReponse"] = "automationsReponse"
    automations: dict[str, dict[Literal["input", "output", "hidden"], Any]]


class AutomationModel(BaseModel):
    path: str
    provider: Callable
    inputModel: type[ParameterSet]
    outputModel: type[ProcessStreamItem]
    interfaceModel: Callable[[], list[HoudiniParmTemplateSpecType]] | None = None
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
    def interface_model(self) -> Callable[[], list[HoudiniParmTemplateSpecType]] | None:
        """Snake-case alias for new code."""

        return self.interfaceModel


class AutomationRequest(BaseModel):
    """
    Contract for requests for work, results will be published back to
    results_subject if specified.
    """

    process_guid: str
    correlation: str
    results_subject: str | None = None
    job_id: str | None = None
    auth_token: str | None = None
    path: str
    data: dict
    telemetry_context: dict | None = Field(default_factory=dict)
    event_id: str | None = None


class BulkAutomationRequest(BaseModel):
    """Bulk automation-jobs in one requests"""

    is_bulk_processing: bool = True
    requests: list[AutomationRequest] = Field(default_factory=list)
    event_id: str | None = None
    telemetry_context: dict | None = Field(default_factory=dict)


class AutomationRequestResult(BaseModel):
    processed: bool = False
    request: AutomationRequest | None = None
    result: dict | None = None


class EventAutomationResponse(BaseModel):
    """Bulk automation-jobs in one requests"""

    is_bulk_processing: bool = False
    processed: bool = False
    request_result: list[AutomationRequestResult] = Field(default_factory=list)


class CropImageRequest(ParameterSet):
    image_file: FileParameter
    src_asset_id: str
    src_version: list[int]
    crop_pos_x: IntParameterSpec | None = None
    crop_pos_y: IntParameterSpec | None = None
    crop_w: IntParameterSpec
    crop_h: IntParameterSpec
