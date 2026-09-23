"""Deployment switch for the embedded agent runtime."""

import os

from lib.infra.api_errors import ServiceUnavailableError


def agent_enabled() -> bool:
    """Only an explicit false value disables the embedded agent."""
    return os.environ.get("ARCREEL_AGENT_ENABLED", "true").strip().lower() != "false"


def require_agent_enabled() -> None:
    """Reject agent operations before any runtime work is performed."""
    if not agent_enabled():
        raise ServiceUnavailableError("agent_disabled")
