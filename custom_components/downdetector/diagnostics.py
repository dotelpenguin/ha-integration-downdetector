"""Diagnostics for Downdetector."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import DowndetectorConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: DowndetectorConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "last_exception": repr(coordinator.last_exception),
        "last_http_status": coordinator.client.last_status,
        "last_html_size": coordinator.client.last_html_size,
        "snapshot": None
        if data is None
        else {
            "calculated_at": data.calculated_at,
            "raw_count": data.raw_count,
            "services": [s.as_dict() for s in data.services],
        },
    }
