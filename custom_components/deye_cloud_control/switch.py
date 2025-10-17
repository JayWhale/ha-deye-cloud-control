"""Switch platform for Deye Cloud Control integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DeyeCloudApiError
from .const import COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Deye Cloud switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # Add solar sell switch for each device
    for device_sn in coordinator.devices:
        entities.append(
            DeyeCloudSolarSellSwitch(
                coordinator=coordinator,
                device_sn=device_sn,
            )
        )

    async_add_entities(entities)


class DeyeCloudSolarSellSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Deye Cloud Solar Sell Switch."""

    _attr_assumed_state = True  # We can't read the actual state from API

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = "Deye Solar Sell"
        self._attr_unique_id = f"{device_sn}_solar_sell"
        self._attr_icon = "mdi:solar-power"
        self._is_on = None  # Track state locally since API doesn't provide it

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        # Try to read from system config if available
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        config = device_data.get("config", {})
        
        # Check for solarSellEnable in config
        solar_sell_config = config.get("solarSellEnable")
        if solar_sell_config is not None:
            return bool(solar_sell_config)
        
        # Otherwise use our locally tracked state
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self.coordinator.client.set_solar_sell(
                device_sn=self._device_sn,
                enabled=True,
            )
            self._is_on = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to enable solar sell: %s", err)
            # Revert optimistic state on error
            self._is_on = None
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self.coordinator.client.set_solar_sell(
                device_sn=self._device_sn,
                enabled=False,
            )
            self._is_on = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to disable solar sell: %s", err)
            # Revert optimistic state on error
            self._is_on = None
            self.async_write_ha_state()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        info = device_data.get("info", {})
        
        return {
            "identifiers": {(DOMAIN, self._device_sn)},
            "name": f"INVERTER {self._device_sn}",
            "manufacturer": "Deye",
            "model": info.get("deviceType", "Inverter"),
            "serial_number": self._device_sn,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._device_sn in self.coordinator.data.get("devices", {})
        )
