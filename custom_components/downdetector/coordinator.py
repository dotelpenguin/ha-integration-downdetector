"""Data update coordinator for Downdetector."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    DowndetectorBlockedError,
    DowndetectorClient,
    DowndetectorError,
    Snapshot,
)
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type DowndetectorConfigEntry = ConfigEntry[DowndetectorCoordinator]


def scan_interval_minutes(entry: ConfigEntry) -> int:
    """Read the configured interval, clamped to the allowed range."""
    value = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    return max(MIN_SCAN_INTERVAL, min(MAX_SCAN_INTERVAL, value))


class DowndetectorCoordinator(DataUpdateCoordinator[Snapshot]):
    """Polls the Downdetector homepage."""

    config_entry: DowndetectorConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: DowndetectorConfigEntry,
        client: DowndetectorClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval_minutes(entry)),
        )
        self.client = client

    async def _async_update_data(self) -> Snapshot:
        try:
            return await self.client.async_get_snapshot()
        except DowndetectorBlockedError as err:
            raise UpdateFailed(
                f"{err}. Cloudflare may be blocking this host; will retry next interval"
            ) from err
        except DowndetectorError as err:
            raise UpdateFailed(str(err)) from err
