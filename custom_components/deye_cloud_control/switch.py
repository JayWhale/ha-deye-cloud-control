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

    # Add battery charge mode switch for each device
    for device_sn in coordinator.devices:
        entities.append(
            DeyeCloudBatteryChargeModeSwitch(
                coordinator=coordinator,
                device_sn=device_sn,
            )
        )

    async_add_entities(entities)


class DeyeCloudBatteryChargeModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Deye Cloud Battery Charge Mode Switch."""

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = f"{self._get_device_name()} Battery Charge Mode"
        self._attr_unique_id = f"{device_sn}_battery_charge_mode"
        self._attr_icon = "mdi:battery-charging"

    def _get_device_name(self) -> str:
        """Get device name."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        return device_data.get("info", {}).get("deviceName", f"Device {self._device_sn}")

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        
        # First try data, then config
        data = device_data.get("data", {})
        config = device_data.get("config", {})
        
        # Try different possible keys for charge mode
        charge_mode = (
            data.get("chargeMode") or 
            data.get("ChargeMode") or 
            data.get("BatteryChargeMode") or
            config.get("chargeMode") or
            config.get("enableGridCharge")
        )
        
        if charge_mode is not None:
            # Handle both boolean and string values
            if isinstance(charge_mode, str):
                return charge_mode.lower() in ["true", "1", "on", "enabled"]
            return bool(charge_mode)
        
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self.coordinator.client.set_battery_mode(
                device_sn=self._device_sn,
                charge_mode=True,
            )
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to turn on battery charge mode: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self.coordinator.client.set_battery_mode(
                device_sn=self._device_sn,
                charge_mode=False,
            )
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to turn off battery charge mode: %s", err)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        info = device_data.get("info", {})
        
        return {
            "identifiers": {(DOMAIN, self._device_sn)},
            "name": self._get_device_name(),
            "manufacturer": "Deye",
            "model": info.get("deviceModel", "Inverter"),
            "sw_version": info.get("firmwareVersion"),
            "serial_number": self._device_sn,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._device_sn in self.coordinator.data.get("devices", {})
        )
