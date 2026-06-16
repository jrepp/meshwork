from collections.abc import Iterator

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


@pytest.fixture(scope="session")
def nats_url() -> Iterator[str]:
    try:
        with DockerContainer("nats:2-alpine").with_exposed_ports(4222) as container:
            wait_for_logs(container, "Server is ready", timeout=20)
            host = container.get_container_host_ip()
            port = container.get_exposed_port(4222)
            yield f"nats://{host}:{port}"
    except Exception as exc:
        pytest.skip(f"Docker/Testcontainers NATS unavailable: {exc}")
