"""Config flow for Deye Cloud Control integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import DeyeCloudApiClient
from .const import (
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REGION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    REGION_EU,
    REGIONS,
)

_LOGGER = logging.getLogger(__name__)


class DeyeCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Deye Cloud Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Get the base URL for the selected region
            region = user_input[CONF_REGION]
            base_url = REGIONS[region]["base_url"]

            # Create API client to test connection
            client = DeyeCloudApiClient(
                app_id=user_input[CONF_APP_ID],
                app_secret=user_input[CONF_APP_SECRET],
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
                base_url=base_url,
            )

            try:
                # Test the connection
                if await client.test_connection():
                    await client.close()
                    
                    # Create the config entry
                    return self.async_create_entry(
                        title=f"Deye Cloud ({REGIONS[region]['name']})",
                        data=user_input,
                    )
                else:
                    errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"
            finally:
                await client.close()

        # Build region options for dropdown
        region_options = [
            selector.SelectOptionDict(value=region_id, label=region_data["name"])
            for region_id, region_data in REGIONS.items()
        ]

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=REGION_EU): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=region_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_APP_ID): str,
                vol.Required(CONF_APP_SECRET): str,
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "info": "Get your App ID and App Secret from https://developer.deyecloud.com/app. Select your data center region.",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "DeyeCloudOptionsFlow":
        """Get the options flow for this handler."""
        return DeyeCloudOptionsFlow(config_entry)


class DeyeCloudOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Deye Cloud Control."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
