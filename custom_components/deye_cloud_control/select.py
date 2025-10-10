"""Select platform for Deye Cloud Control integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DeyeCloudApiError
from .const import (
    COORDINATOR,
    DOMAIN,
    ENERGY_PATTERNS,
    WORK_MODES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Deye Cloud select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # Add selects for each device
    for device_sn in coordinator.devices:
        entities.extend([
            DeyeCloudWorkModeSelect(
                coordinator=coordinator,
                device_sn=device_sn,
            ),
            DeyeCloudEnergyPatternSelect(
                coordinator=coordinator,
                device_sn=device_sn,
            ),
        ])

    async_add_entities(entities)


class DeyeCloudWorkModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Deye Cloud Work Mode Select."""

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = f"{self._get_device_name()} Work Mode"
        self._attr_unique_id = f"{device_sn}_work_mode"
        self._attr_options = WORK_MODES
        self._attr_icon = "mdi:cog"

    def _get_device_name(self) -> str:
        """Get device name."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        return device_data.get("info", {}).get("deviceName", f"Device {self._device_sn}")

    @property
    def current_option(self) -> str | None:
        """Return the selected option."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        data = device_data.get("data", {})
        work_mode = data.get("workMode")
        
        if work_mode in WORK_MODES:
            return work_mode
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in WORK_MODES:
            _LOGGER.error("Invalid work mode: %s", option)
            return

        try:
            await self.coordinator.client.set_work_mode(
                device_sn=self._device_sn,
                work_mode=option,
            )
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to set work mode: %s", err)

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


class DeyeCloudEnergyPatternSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Deye Cloud Energy Pattern Select."""

    def __init__(self, coordinator, device_sn: str) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._attr_name = f"{self._get_device_name()} Energy Pattern"
        self._attr_unique_id = f"{device_sn}_energy_pattern"
        self._attr_options = ENERGY_PATTERNS
        self._attr_icon = "mdi:battery-arrow-up"

    def _get_device_name(self) -> str:
        """Get device name."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        return device_data.get("info", {}).get("deviceName", f"Device {self._device_sn}")

    @property
    def current_option(self) -> str | None:
        """Return the selected option."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        data = device_data.get("data", {})
        energy_pattern = data.get("energyPattern")
        
        if energy_pattern in ENERGY_PATTERNS:
            return energy_pattern
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in ENERGY_PATTERNS:
            _LOGGER.error("Invalid energy pattern: %s", option)
            return

        try:
            await self.coordinator.client.set_energy_pattern(
                device_sn=self._device_sn,
                energy_pattern=option,
            )
            await self.coordinator.async_request_refresh()
        except DeyeCloudApiError as err:
            _LOGGER.error("Failed to set energy pattern: %s", err)

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
