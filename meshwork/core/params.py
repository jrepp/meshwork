"""Generic Meshwork parameter models.

These types intentionally avoid Houdini-specific template models. Houdini
interface generation lives under `meshwork.houdini`.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ParameterSpecModel(BaseModel):
    param_type: str
    label: str
    category_label: str | None = None
    constant: bool = False


class IntParameterSpec(ParameterSpecModel):
    param_type: Literal["int"] = "int"
    default: int | list[int] = 0
    min: int | None = None
    max: int | None = None


class FloatParameterSpec(ParameterSpecModel):
    param_type: Literal["float"] = "float"
    default: float | list[float] = 0.0
    min: float | None = None
    max: float | None = None


class StringParameterSpec(ParameterSpecModel):
    param_type: Literal["string"] = "string"
    default: str | list[str] = ""


class BoolParameterSpec(ParameterSpecModel):
    param_type: Literal["bool"] = "bool"
    default: bool = False


class EnumValueSpec(BaseModel):
    name: str
    label: str


class EnumParameterSpec(ParameterSpecModel):
    param_type: Literal["enum"] = "enum"
    values: list[EnumValueSpec]
    default: str


class FileParameterSpec(ParameterSpecModel):
    param_type: Literal["file"] = "file"
    name: str | None = ""
    type: list[str] | None = None
    default: str | list[str] = ""


class RampPointSpec(BaseModel):
    pos: float
    c: list[float] | None = None
    value: float | None = None
    interp: str = "Linear"


class RampParameterSpec(ParameterSpecModel):
    param_type: Literal["ramp"] = "ramp"
    ramp_parm_type: str = "Float"
    default: list[RampPointSpec] = Field(default_factory=list)


ParameterSpecType = Annotated[
    IntParameterSpec
    | FloatParameterSpec
    | StringParameterSpec
    | BoolParameterSpec
    | EnumParameterSpec
    | FileParameterSpec
    | RampParameterSpec,
    Field(discriminator="param_type"),
]


class FileParameter(BaseModel):
    file_id: str
    file_path: str | None = None


ParameterType = (int, float, str, bool, FileParameter)


class ParameterSet(BaseModel):
    model_config = ConfigDict(extra="allow")

    @classmethod
    def _parameter_spec_for_annotation(
        cls, name: str, annotation: Any
    ) -> ParameterSpecType | None:
        if annotation is int:
            return IntParameterSpec(label=name)
        if annotation is float:
            return FloatParameterSpec(label=name)
        if annotation is str:
            return StringParameterSpec(label=name)
        if annotation is bool:
            return BoolParameterSpec(label=name)
        if annotation is FileParameter:
            return FileParameterSpec(name=name, label=name)
        return None

    @classmethod
    def get_parameter_specs(cls) -> list[ParameterSpecType]:
        specs: list[ParameterSpecType] = []
        for name, field in cls.model_fields.items():
            spec = cls._parameter_spec_for_annotation(name, field.annotation)
            if spec is not None:
                specs.append(spec)
        return specs

    @classmethod
    def parameter_spec(cls) -> "ParameterSpec":
        """Return named parameter metadata for this request model."""

        params = {}
        for name, field in cls.model_fields.items():
            spec = cls._parameter_spec_for_annotation(name, field.annotation)
            if spec is not None:
                params[name] = spec
        try:
            default = cls()
        except Exception:
            default = None
        return ParameterSpec(params=params, default=default)

    @model_validator(mode="before")
    @classmethod
    def check_parameter_types(cls, values: dict) -> Any:
        def check(field: str, value: Any) -> None:
            if isinstance(value, (list, tuple, set, frozenset)):
                for item in value:
                    check(field, item)
            elif isinstance(value, dict):
                try:
                    FileParameter(**value)
                except Exception:
                    for key, item in value.items():
                        check(f"{field}:{key}", item)
            elif not isinstance(value, ParameterType):
                raise TypeError(
                    f"Field '{field}' contains invalid type: {type(value)}. "
                    f"Must match {ParameterType}."
                )

        for name, value in values.items():
            check(name, value)
        return values


class ParameterSpec(BaseModel):
    params: dict[str, ParameterSpecType]
    default: ParameterSet | None = Field(default_factory=ParameterSet)
    hidden: dict[str, bool] | None = Field(default_factory=dict)


__all__ = [
    "BoolParameterSpec",
    "EnumParameterSpec",
    "EnumValueSpec",
    "FileParameter",
    "FileParameterSpec",
    "FloatParameterSpec",
    "IntParameterSpec",
    "ParameterSet",
    "ParameterSpec",
    "ParameterSpecModel",
    "RampParameterSpec",
    "RampPointSpec",
    "StringParameterSpec",
]
