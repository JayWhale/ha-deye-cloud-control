"""Config flow for Deye Cloud Control integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import DeyeCloudApiError, DeyeCloudAuthError, DeyeCloudClient
from .const import (
    CONF_APP_ID,
    CONF_APP_SECRET,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class DeyeCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Deye Cloud Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()

            # Validate credentials
            try:
                client = DeyeCloudClient(
                    app_id=user_input[CONF_APP_ID],
                    app_secret=user_input[CONF_APP_SECRET],
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                )
                await client.obtain_token()
                await client.close()

                return self.async_create_entry(
                    title=f"Deye Cloud Control ({user_input[CONF_EMAIL]})",
                    data=user_input,
                )
            except DeyeCloudAuthError:
                errors["base"] = "invalid_auth"
            except DeyeCloudApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_APP_ID): str,
                    vol.Required(CONF_APP_SECRET): str,
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        errors = {}
        
        # Get the config entry being reconfigured
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            # Validate credentials
            try:
                client = DeyeCloudClient(
                    app_id=user_input[CONF_APP_ID],
                    app_secret=user_input[CONF_APP_SECRET],
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                )
                await client.obtain_token()
                await client.close()

                # Update the config entry
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, **user_input},
                )
                
                # Reload the integration
                await self.hass.config_entries.async_reload(entry.entry_id)
                
                return self.async_abort(reason="reconfigure_successful")
                
            except DeyeCloudAuthError:
                errors["base"] = "invalid_auth"
            except DeyeCloudApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form with current values as defaults
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_APP_ID,
                        default=entry.data.get(CONF_APP_ID, "")
                    ): str,
                    vol.Required(
                        CONF_APP_SECRET,
                        default=entry.data.get(CONF_APP_SECRET, "")
                    ): str,
                    vol.Required(
                        CONF_EMAIL,
                        default=entry.data.get(CONF_EMAIL, "")
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                }
            ),
            errors=errors,
            description_placeholders={
                "info": "Update your Deye Cloud credentials. Get your App ID and App Secret from https://developer.deyecloud.com/app",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> DeyeCloudOptionsFlow:
        """Get the options flow for this handler."""
        return DeyeCloudOptionsFlow(config_entry)


class DeyeCloudOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Deye Cloud Control."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL,
                            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                }
            ),
        )
