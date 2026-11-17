"""Pulse sensor for Downdetector."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import TOP_N
from .coordinator import DowndetectorConfigEntry, DowndetectorCoordinator
from .entity import DowndetectorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DowndetectorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor."""
    async_add_entities([DowndetectorPulseSensor(entry.runtime_data)])


class DowndetectorPulseSensor(DowndetectorEntity, SensorEntity):
    """State = number of top-16 services currently flagged 'danger'.

    Attributes carry the top 16 list and an 'impacted' list (danger/warning,
    sorted by biggest jump over baseline) for dashboards and automations.
    """

    _attr_translation_key = "pulse"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "services"
    # Large lists: keep them on the live state, out of the recorder database.
    _unrecorded_attributes = frozenset({"services", "impacted"})

    def __init__(self, coordinator: DowndetectorCoordinator) -> None:
        super().__init__(coordinator, "pulse")

    @property
    def native_value(self) -> int | None:
        if (data := self.coordinator.data) is None:
            return None
        return data.danger_count(TOP_N)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if (data := self.coordinator.data) is None:
            return None
        top = data.top(TOP_N)
        impacted = data.impacted(TOP_N)
        biggest = impacted[0] if impacted else (max(top, key=lambda s: s.trend) if top else None)
        return {
            "top_service": biggest.name if biggest else None,
            "top_reports": biggest.reports if biggest else None,
            "top_trend": biggest.trend if biggest else None,
            "impacted_count": len(impacted),
            "calculated_at": data.calculated_at,
            "impacted": [s.as_dict() for s in impacted],
            "services": [s.as_dict() for s in top],
        }
