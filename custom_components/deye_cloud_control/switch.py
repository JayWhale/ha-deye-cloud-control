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

    _attr_device_class = None  # Simple switch, no special device class

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = "Deye Battery Charging Mode"
        self._attr_unique_id = f"{device_sn}_battery_charge_mode"
        self._attr_icon = "mdi:battery-charging"
        self._state = None  # Track state locally

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        data = device_data.get("data", {})
        config = device_data.get("config", {})
        
        # Log ALL keys we're getting from the API for debugging
        _LOGGER.warning(
            "Battery Charge Mode DEBUG - ALL data keys: %s",
            list(data.keys())
        )
        _LOGGER.warning(
            "Battery Charge Mode DEBUG - ALL config keys: %s",
            list(config.keys())
        )
        
        # Try different possible keys for charge mode
        charge_mode = (
            data.get("chargeMode") or 
            data.get("ChargeMode") or 
            data.get("BatteryChargeMode") or
            data.get("batteryChargeMode") or
            config.get("chargeMode") or
            config.get("batteryChargeMode") or
            config.get("ChargeMode")
        )
        
        _LOGGER.debug("Battery Charge Mode raw value: %s (type: %s)", charge_mode, type(charge_mode))
        
        if charge_mode is not None:
            # Handle both boolean and string values
            if isinstance(charge_mode, str):
                result = charge_mode.lower() in ["true", "1", "on", "enabled", "enable"]
                _LOGGER.debug("Battery Charge Mode parsed as: %s", result)
                self._state = result
                return result
            result = bool(charge_mode)
            _LOGGER.debug("Battery Charge Mode boolean: %s", result)
            self._state = result
            return result
        
        # If we can't get state from API, return last known state
        _LOGGER.warning("Battery Charge Mode - No state found in API response, using cached state: %s", self._state)
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            _LOGGER.info("Turning ON battery charge mode for device %s", self._device_sn)
            await self.coordinator.client.set_battery_mode(
                device_sn=self._device_sn,
                charge_mode=True,
            )
            self._state = True  # Update local state immediately
            self.async_write_ha_state()  # Update UI immediately
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to enable battery charge mode: %s", err)
            self._state = False  # Revert on error

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            _LOGGER.info("Turning OFF battery charge mode for device %s", self._device_sn)
            await self.coordinator.client.set_battery_mode(
                device_sn=self._device_sn,
                charge_mode=False,
            )
            self._state = False  # Update local state immediately
            self.async_write_ha_state()  # Update UI immediately
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to disable battery charge mode: %s", err)
            self._state = True  # Revert on error

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

    _attr_device_class = None  # Simple switch, no special device class

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = "Deye Solar Sell"
        self._attr_unique_id = f"{device_sn}_solar_sell"
        self._attr_icon = "mdi:solar-power"
        self._state = None  # Track state locally

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        data = device_data.get("data", {})
        config = device_data.get("config", {})
        
        # Log ALL keys we're getting from the API for debugging
        _LOGGER.warning(
            "Solar Sell DEBUG - ALL data keys: %s",
            list(data.keys())
        )
        _LOGGER.warning(
            "Solar Sell DEBUG - ALL config keys: %s",
            list(config.keys())
        )
        
        # Try different possible keys for solar sell
        solar_sell = (
            data.get("solarSell") or 
            data.get("SolarSell") or 
            data.get("solarSellEnable") or
            data.get("SolarSellEnable") or
            config.get("solarSell") or
            config.get("solarSellEnable") or
            config.get("SolarSellEnable")
        )
        
        _LOGGER.debug("Solar Sell raw value: %s (type: %s)", solar_sell, type(solar_sell))
        
        if solar_sell is not None:
            # Handle both boolean and string values
            if isinstance(solar_sell, str):
                result = solar_sell.lower() in ["true", "1", "on", "enabled", "enable"]
                _LOGGER.debug("Solar Sell parsed as: %s", result)
                self._state = result
                return result
            result = bool(solar_sell)
            _LOGGER.debug("Solar Sell boolean: %s", result)
            self._state = result
            return result
        
        # If we can't get state from API, return last known state
        _LOGGER.warning("Solar Sell - No state found in API response, using cached state: %s", self._state)
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            _LOGGER.info("Turning ON solar sell for device %s", self._device_sn)
            await self.coordinator.client.set_solar_sell(
                device_sn=self._device_sn,
                enabled=True,
            )
            self._state = True  # Update local state immediately
            self.async_write_ha_state()  # Update UI immediately
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to enable solar sell: %s", err)
            self._state = False  # Revert on error

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            _LOGGER.info("Turning OFF solar sell for device %s", self._device_sn)
            await self.coordinator.client.set_solar_sell(
                device_sn=self._device_sn,
                enabled=False,
            )
            self._state = False  # Update local state immediately
            self.async_write_ha_state()  # Update UI immediately
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to disable solar sell: %s", err)
            self._state = True  # Revert on error

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
