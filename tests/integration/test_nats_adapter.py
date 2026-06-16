import asyncio
import json

import nats
import pytest

from meshwork.automation.adapters import NatsAdapter


async def wait_for_messages(received: list[dict], count: int = 1) -> None:
    for _ in range(50):
        if len(received) >= count:
            return
        await asyncio.sleep(0.1)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nats_adapter_round_trip_with_container(nats_url: str) -> None:
    adapter = NatsAdapter(nats_url=nats_url)
    received: list[dict] = []

    async def callback(payload: dict) -> None:
        received.append(payload)

    await adapter.listen("meshwork.integration", callback)
    try:
        await adapter.post("meshwork.integration", {"message": "hello"})
        await wait_for_messages(received)
    finally:
        await adapter.stop_listening("meshwork.integration")

    assert received == [{"message": "hello"}]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nats_adapter_entity_scoped_round_trip_with_container(
    nats_url: str,
) -> None:
    adapter = NatsAdapter(nats_url=nats_url)
    received: list[dict] = []

    async def callback(payload: dict) -> None:
        received.append(payload)

    await adapter.listen_as("meshwork.integration.entity", "worker-a", callback)
    try:
        await adapter.post_to(
            "meshwork.integration.entity", "worker-b", {"message": "ignored"}
        )
        await adapter.post_to(
            "meshwork.integration.entity", "worker-a", {"message": "targeted"}
        )
        await wait_for_messages(received)
    finally:
        await adapter.stop_listening("meshwork.integration.entity", entity="worker-a")

    assert received == [{"message": "targeted"}]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nats_adapter_receives_direct_nats_publish(nats_url: str) -> None:
    adapter = NatsAdapter(nats_url=nats_url)
    received: list[dict] = []

    async def callback(payload: dict) -> None:
        received.append(payload)

    await adapter.listen("meshwork.integration.direct", callback)
    scoped_subject = adapter._scoped_subject("meshwork.integration.direct")
    nc = await nats.connect(servers=[nats_url])
    try:
        await nc.publish(
            scoped_subject,
            json.dumps({"message": "from-direct-client"}).encode("utf-8"),
        )
        await nc.flush()
        await wait_for_messages(received)
    finally:
        await nc.drain()
        await adapter.stop_listening("meshwork.integration.direct")

    assert received == [{"message": "from-direct-client"}]
