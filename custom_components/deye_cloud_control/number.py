"""Number platform for Deye Cloud Control integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower
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
    """Set up Deye Cloud Control number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # Add battery current limit numbers and max sell power for each device
    for device_sn in coordinator.devices:
        entities.extend([
            DeyeCloudMaxChargeCurrent(
                coordinator=coordinator,
                device_sn=device_sn,
            ),
            DeyeCloudMaxDischargeCurrent(
                coordinator=coordinator,
                device_sn=device_sn,
            ),
            DeyeCloudMaxSellPower(
                coordinator=coordinator,
                device_sn=device_sn,
            ),
        ])

    async_add_entities(entities)


class DeyeCloudMaxChargeCurrent(CoordinatorEntity, NumberEntity):
    """Representation of battery max charge current setting."""

    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_icon = "mdi:battery-charging"

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = "Deye Max Charge Current"
        self._attr_unique_id = f"{device_sn}_max_charge_current"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 200
        self._attr_native_step = 1

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        config = device_data.get("config", {})
        
        # Try different possible keys
        max_charge = (
            config.get("maxChargeCurrent") or
            config.get("MaxChargeCurrent") or
            config.get("chargeCurrentLimit")
        )
        
        if max_charge is not None:
            try:
                return float(max_charge)
            except (ValueError, TypeError):
                return None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            await self.coordinator.client.set_battery_charge_current(
                device_sn=self._device_sn,
                current=int(value),
            )
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to set max charge current: %s", err)

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


class DeyeCloudMaxDischargeCurrent(CoordinatorEntity, NumberEntity):
    """Representation of battery max discharge current setting."""

    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_icon = "mdi:battery-minus"

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = "Deye Max Discharge Current"
        self._attr_unique_id = f"{device_sn}_max_discharge_current"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 200
        self._attr_native_step = 1

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        config = device_data.get("config", {})
        
        # Try different possible keys
        max_discharge = (
            config.get("maxDischargeCurrent") or
            config.get("MaxDischargeCurrent") or
            config.get("dischargeCurrentLimit")
        )
        
        if max_discharge is not None:
            try:
                return float(max_discharge)
            except (ValueError, TypeError):
                return None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            await self.coordinator.client.set_battery_discharge_current(
                device_sn=self._device_sn,
                current=int(value),
            )
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to set max discharge current: %s", err)

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


class DeyeCloudMaxSellPower(CoordinatorEntity, NumberEntity):
    """Representation of max sell power setting."""

    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_icon = "mdi:transmission-tower-export"

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = "Deye Max Sell Power"
        self._attr_unique_id = f"{device_sn}_max_sell_power"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 20000
        self._attr_native_step = 100

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        data = device_data.get("data", {})
        config = device_data.get("config", {})
        
        max_sell = (
            data.get("maxSellPower") or 
            data.get("MaxSellPower") or
            config.get("maxSellPower")
        )
        
        if max_sell is not None:
            try:
                return float(max_sell)
            except (ValueError, TypeError):
                return None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            await self.coordinator.client.set_max_sell_power(
                device_sn=self._device_sn,
                power=int(value),
            )
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to set max sell power: %s", err)

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
