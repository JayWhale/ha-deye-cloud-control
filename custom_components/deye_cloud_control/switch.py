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

    # Add battery charge mode switch and solar sell switch for each device
    for device_sn in coordinator.devices:
        entities.extend([
            DeyeCloudBatteryChargeModeSwitch(
                coordinator=coordinator,
                device_sn=device_sn,
            ),
            DeyeCloudSolarSellSwitch(
                coordinator=coordinator,
                device_sn=device_sn,
            ),
        ])

    async_add_entities(entities)


class DeyeCloudBatteryChargeModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Deye Cloud Battery Charge Mode Switch."""

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = "Deye Battery Charging Mode"
        self._attr_unique_id = f"{device_sn}_battery_charge_mode"
        self._attr_icon = "mdi:battery-charging"
        # Default to OFF, will be updated when we get real state
        self._attr_is_on = False
        self._attr_assumed_state = True  # Tell HA we don't have definitive state

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        # Return the assumed state
        return self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            _LOGGER.info("Enabling battery charge mode for device %s", self._device_sn)
            await self.coordinator.client.set_battery_mode(
                device_sn=self._device_sn,
                charge_mode=True,
            )
            self._attr_is_on = True
            self.async_write_ha_state()
            # Refresh to get updated state from API
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to enable battery charge mode: %s", err)
            # Don't change state on error

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            _LOGGER.info("Disabling battery charge mode for device %s", self._device_sn)
            await self.coordinator.client.set_battery_mode(
                device_sn=self._device_sn,
                charge_mode=False,
            )
            self._attr_is_on = False
            self.async_write_ha_state()
            # Refresh to get updated state from API
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to disable battery charge mode: %s", err)
            # Don't change state on error

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


class DeyeCloudSolarSellSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Deye Cloud Solar Sell Switch."""

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = "Deye Solar Sell"
        self._attr_unique_id = f"{device_sn}_solar_sell"
        self._attr_icon = "mdi:solar-power"
        # Default to ON (selling enabled), will be updated when we get real state
        self._attr_is_on = True
        self._attr_assumed_state = True  # Tell HA we don't have definitive state

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        # Return the assumed state
        return self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            _LOGGER.info("Enabling solar sell for device %s", self._device_sn)
            await self.coordinator.client.set_solar_sell(
                device_sn=self._device_sn,
                enabled=True,
            )
            self._attr_is_on = True
            self.async_write_ha_state()
            # Refresh to get updated state from API
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to enable solar sell: %s", err)
            # Don't change state on error

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            _LOGGER.info("Disabling solar sell for device %s", self._device_sn)
            await self.coordinator.client.set_solar_sell(
                device_sn=self._device_sn,
                enabled=False,
            )
            self._attr_is_on = False
            self.async_write_ha_state()
            # Refresh to get updated state from API
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to disable solar sell: %s", err)
            # Don't change state on error

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
