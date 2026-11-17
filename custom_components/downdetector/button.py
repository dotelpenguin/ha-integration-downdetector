"""Refresh-now button for Downdetector."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DowndetectorConfigEntry, DowndetectorCoordinator
from .entity import DowndetectorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DowndetectorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the button."""
    async_add_entities([DowndetectorRefreshButton(entry.runtime_data)])


class DowndetectorRefreshButton(DowndetectorEntity, ButtonEntity):
    """Triggers an immediate refresh."""

    _attr_translation_key = "refresh"

    def __init__(self, coordinator: DowndetectorCoordinator) -> None:
        super().__init__(coordinator, "refresh")

    @property
    def available(self) -> bool:
        """Always pressable, even if the last update failed."""
        return True

    async def async_press(self) -> None:
        """Fetch now."""
        await self.coordinator.async_refresh()
