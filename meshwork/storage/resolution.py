"""File resolution helpers."""

from meshwork.core.params import FileParameter
from meshwork.runtime.params import download_file, resolve_params


class HttpFileResolver:
    """Resolve Meshwork file parameters through an HTTP download endpoint."""

    def __init__(self, endpoint: str, headers: dict | None = None) -> None:
        self.endpoint = endpoint
        self.headers = headers or {}

    def resolve(self, value: FileParameter, directory: str) -> FileParameter:
        value.file_path = download_file(
            self.endpoint, directory, value.file_id, self.headers
        )
        return value


__all__ = ["HttpFileResolver", "download_file", "resolve_params"]
