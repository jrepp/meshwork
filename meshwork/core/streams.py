"""Generic Meshwork stream models."""

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class StreamItem(BaseModel):
    item_type: str
    index: str | None = None
    correlation: str = Field(default_factory=lambda: str(uuid4()))


class ProcessStreamItem(StreamItem):
    process_guid: str = ""
    job_id: str = ""


class Progress(ProcessStreamItem):
    item_type: Literal["progress"] = "progress"
    progress: int = 0


class Message(ProcessStreamItem):
    item_type: Literal["message"] = "message"
    message: str = ""


class Error(ProcessStreamItem):
    item_type: Literal["error"] = "error"
    error: str = ""


class OutputFiles(ProcessStreamItem):
    item_type: Literal["file"] = "file"
    files: dict[str, list[str]] = Field(default_factory=dict)


class FileContentChunk(ProcessStreamItem):
    item_type: Literal["file_content_chunk"] = "file_content_chunk"
    file_key: str
    file_index: int
    chunk_index: int
    total_chunks: int
    file_size: int
    encoded_data: str


class JobDefinition(ProcessStreamItem):
    item_type: Literal["job_def"] = "job_def"
    job_def_id: str = ""
    job_type: str
    name: str
    description: str
    parameter_spec: Any
    owner_id: str | None = None
    source: Any = None


class Event(StreamItem):
    item_type: Literal["event"] = "event"
    payload: dict[str, Any] = Field(default_factory=dict)
    event_type: str | None = None
    queued: datetime | None = None
    acked: datetime | None = None
    completed: datetime | None = None


__all__ = [
    "Error",
    "Event",
    "FileContentChunk",
    "JobDefinition",
    "Message",
    "OutputFiles",
    "ProcessStreamItem",
    "Progress",
    "StreamItem",
]
