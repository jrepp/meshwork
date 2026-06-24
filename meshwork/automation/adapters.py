import json
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias

import nats
import requests
from nats.aio.client import Client as NatsClient
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription

from gcid import location
from meshwork.automation.utils import format_exception
from meshwork.core.protocols import Payload

log = logging.getLogger(__name__)

NATS_URL = os.environ.get("NATS_ENDPOINT", "nats://localhost:4222")
MessageCallback: TypeAlias = Callable[[Payload], Awaitable[None]]
JsonResponse: TypeAlias = Any
SUCCESS_STATUS_CODES = {200, 201}


class NatsAdapter:
    def __init__(self, nats_url: str = NATS_URL) -> None:
        self.nats_url = nats_url
        self.listeners: dict[str, Subscription] = {}
        self.nc: NatsClient | None = None
        self.env = os.getenv("MYTHICA_ENVIRONMENT", "debug")
        self.location = location.location()

    async def _connect(self) -> None:
        """Establish a connection to NATS."""
        if not self.nc:
            log.debug("Connecting to NATS, nats_url: %s", self.nats_url)
            self.nc = await nats.connect(servers=[self.nats_url])
            log.info("Connected to NATS")

    async def _disconnect(self) -> None:
        """Disconnect from NATS gracefully."""
        if self.nc:
            log.debug("Disconnecting from NATS")
            await self.nc.drain()  # Gracefully stop receiving messages
            self.nc = None
            log.info("Disconnected from NATS")

    def _scoped_subject(self, subject: str) -> str:
        """Return a subject that is scoped to the environment and location"""
        return f"{subject}.{self.env}.{self.location}"

    def _scoped_subject_to(self, subject: str, entity: str) -> str:
        """Return a subject that is scoped to a scoped entity"""
        return f"{subject}.{self.env}.{self.location}.{entity}"

    async def _internal_post(self, subject: str, data: Payload) -> None:
        await self._connect()
        p_data = data.copy()
        try:
            assert self.nc is not None
            await self.nc.publish(subject, json.dumps(data).encode())
            # Remove encoded data from the log
            if p_data.get("encoded_data"):
                p_data["encoded_data"] = "..."
            log.info(f"Posted: {subject} - {p_data}")
        except Exception as e:
            log.error(
                f"Sending to NATS failed: {subject} - {p_data} - {format_exception(e)}"
            )
        finally:
            if not self.listeners:
                await self._disconnect()

    async def publish(self, subject: str, payload: Payload) -> None:
        """Publish payload to an environment/location-scoped subject."""

        await self.post(subject, payload)

    async def publish_to(self, subject: str, entity: str, payload: Payload) -> None:
        """Publish payload to an environment/location/entity-scoped subject."""

        await self.post_to(subject, entity, payload)

    async def post(self, subject: str, data: Payload) -> None:
        """Post data to NATS on subject."""
        await self._internal_post(self._scoped_subject(subject), data)

    async def post_to(self, subject: str, entity: str, data: Payload) -> None:
        await self._internal_post(self._scoped_subject_to(subject, entity), data)

    async def listen(self, subject: str, callback: MessageCallback) -> None:
        await self._internal_listen(self._scoped_subject(subject), callback)

    async def listen_as(
        self, subject: str, entity: str, callback: MessageCallback
    ) -> None:
        await self._internal_listen(self._scoped_subject_to(subject, entity), callback)

    async def _internal_listen(self, subject: str, callback: MessageCallback) -> None:
        if subject in self.listeners:
            log.warning(f"NATS listener already active for subject {subject}")
            return

        """ Listen to NATS """
        await self._connect()

        async def message_handler(msg: Msg) -> None:
            try:
                payload = json.loads(msg.data.decode("utf-8"))
                log.info(f"Received message on {subject}: {payload}")
                await callback(payload)
            except Exception as e:
                log.error(
                    f"Error processing message on {subject}: {format_exception(e)}"
                )

        try:
            # Wait for the response with a timeout (customize as necessary)
            log.debug("Setting up NATS response listener")
            assert self.nc is not None
            listener = await self.nc.subscribe(
                subject, queue="worker", cb=message_handler
            )
            self.listeners[subject] = listener
            log.info(f"NATS subscribed to {subject}")

        except Exception as e:
            log.error(
                f"Error setting up listener for subject {subject}: {format_exception(e)}"
            )
            raise

    async def stop_listening(self, subject: str, entity: str | None = None) -> None:
        """Stop listening for a scoped subject created by listen or listen_as."""

        scoped_subject = (
            self._scoped_subject_to(subject, entity)
            if entity is not None
            else self._scoped_subject(subject)
        )
        await self.unlisten(scoped_subject)

    async def unlisten(self, subject: str) -> None:
        """Shut down the listener for a specific subject."""
        if subject in self.listeners:
            log.debug(f"Shutting down listener for subject {subject}")
            subscription = self.listeners.pop(subject)
            await subscription.unsubscribe()
            log.info(f"Listener for subject {subject} shut down")
            if not self.listeners:
                await self._disconnect()
                log.info("Last Listener was shut down. Closing Connection")
        else:
            log.warning(f"No active listener found for subject {subject}")


class RestAdapter:
    def _headers(
        self,
        headers: dict[str, str | None] | None = None,
        *,
        token: str | None = None,
        content_type: str | None = None,
    ) -> dict[str, str | None]:
        result = headers.copy() if headers else {"traceparent": None}
        if token:
            result["Authorization"] = f"Bearer {token}"
        if content_type:
            result["Content-Type"] = content_type
        return result

    def get(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        token: str | None = None,
        headers: dict[str, str | None] | None = None,
    ) -> JsonResponse | None:
        """Get data from an endpoint."""
        data = data or {}
        log.debug(f"Getting from Endpoint: {endpoint} - {data}")
        response = requests.get(
            endpoint,
            headers=self._headers(headers, token=token),
        )
        if response.status_code in SUCCESS_STATUS_CODES:
            log.debug(f"Endpoint Response: {response.status_code}")
            return response.json()
        log.error(
            f"Failed to call job API: {endpoint} - {data} - {response.status_code}"
        )
        return None

    def post(
        self,
        endpoint: str,
        json_data: Any,
        token: str | None,
        headers: dict[str, str | None] | None = None,
        query_params: dict[str, Any] | None = None,
    ) -> JsonResponse | None:
        """Post data to an endpoint synchronously."""
        query_params = query_params or {}
        log.debug(f"posting[{endpoint}]: {json_data}; {headers=}")
        response = requests.post(
            endpoint,
            json=json_data,
            params=query_params,
            headers=self._headers(
                headers, token=token, content_type="application/json"
            ),
        )
        if response.status_code in SUCCESS_STATUS_CODES:
            log.debug(f"Endpoint Response: {response.status_code}")
            return response.json()
        log.error(
            f"Failed to call job API: {endpoint} - {json_data} - {response.status_code}"
        )
        return None

    def post_file(
        self,
        endpoint: str,
        file_data: list[Any],
        token: str | None,
        headers: dict[str, str | None] | None = None,
    ) -> JsonResponse | None:
        """Post file to an endpoint."""
        log.debug(f"Sending file to Endpoint: {endpoint} - {file_data}")
        response = requests.post(
            endpoint,
            files=file_data,
            headers=self._headers(headers, token=token),
        )
        if response.status_code in SUCCESS_STATUS_CODES:
            log.debug(f"Endpoint Response: {response.status_code}")
            return response.json()
        log.error(
            f"Failed to call job API: {endpoint} - {file_data} - {response.status_code}"
        )
        return None
