"""Mythica worker factory."""

from meshwork.automation.automations import get_default_automations
from meshwork.automation.publishers import ResultPublisher, SlimPublisher
from meshwork.automation.worker import Worker
from meshwork.config import meshwork_config, update_headers_from_context
from meshwork.runtime.alerts import send_alert
from meshwork.runtime.params import resolve_params


def create_mythica_worker() -> Worker:
    """Create a worker with the current Mythica-compatible defaults."""

    return Worker(
        default_automations=get_default_automations,
        catalog_path="/mythica/automations",
        api_base_uri_provider=lambda: meshwork_config().api_base_uri,
        headers_provider=update_headers_from_context,
        param_resolver=resolve_params,
        alert_handler=send_alert,
        process_event_results=True,
        publisher_factory=ResultPublisher,
        slim_publisher_factory=SlimPublisher,
        web_title="Automation API",
        web_description="Mythica Automation API",
    )


__all__ = ["Worker", "create_mythica_worker"]
