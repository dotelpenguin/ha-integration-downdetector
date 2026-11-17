"""Config flow for Downdetector."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import (
    DowndetectorBlockedError,
    DowndetectorClient,
    DowndetectorError,
    DowndetectorParseError,
)
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    SCAN_INTERVAL_STEP,
)

_LOGGER = logging.getLogger(__name__)

REGION_US = "us"


def _interval_schema(default: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SCAN_INTERVAL, default=default): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL,
                    max=MAX_SCAN_INTERVAL,
                    step=SCAN_INTERVAL_STEP,
                    mode=NumberSelectorMode.SLIDER,
                    unit_of_measurement="min",
                )
            )
        }
    )


class DowndetectorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Downdetector."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Initial setup: test that the site is reachable, pick the interval."""
        await self.async_set_unique_id(REGION_US)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await DowndetectorClient().async_get_snapshot()
            except DowndetectorBlockedError:
                errors["base"] = "blocked"
            except DowndetectorParseError:
                errors["base"] = "parse_error"
            except DowndetectorError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error testing Downdetector")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="Downdetector (US)",
                    data={},
                    options={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_interval_schema(DEFAULT_SCAN_INTERVAL),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return DowndetectorOptionsFlow()


class DowndetectorOptionsFlow(OptionsFlow):
    """Change the refresh interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the interval slider."""
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])}
            )
        current = int(
            self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        return self.async_show_form(step_id="init", data_schema=_interval_schema(current))
