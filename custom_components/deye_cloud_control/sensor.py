"""Sensor platform for Deye Cloud Control integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Map units from API to Home Assistant units
UNIT_MAP = {
    "W": UnitOfPower.WATT,
    "kW": UnitOfPower.KILO_WATT,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "V": UnitOfElectricPotential.VOLT,
    "A": UnitOfElectricCurrent.AMPERE,
    "Hz": UnitOfFrequency.HERTZ,
    "°C": UnitOfTemperature.CELSIUS,
    "%": PERCENTAGE,
    "VA": "VA",  # Apparent power
}

# Map sensor keys to device classes
DEVICE_CLASS_MAP = {
    "Power": SensorDeviceClass.POWER,
    "Energy": SensorDeviceClass.ENERGY,
    "Voltage": SensorDeviceClass.VOLTAGE,
    "Current": SensorDeviceClass.CURRENT,
    "Frequency": SensorDeviceClass.FREQUENCY,
    "Temperature": SensorDeviceClass.TEMPERATURE,
    "SOC": SensorDeviceClass.BATTERY,
    "BMSSOC": SensorDeviceClass.BATTERY,
}

# Map sensor keys to state classes
STATE_CLASS_MAP = {
    "TotalEnergy": SensorStateClass.TOTAL,
    "TotalProduction": SensorStateClass.TOTAL,
    "TotalConsumption": SensorStateClass.TOTAL,
    "TotalCharge": SensorStateClass.TOTAL,
    "TotalDischarge": SensorStateClass.TOTAL,
    "TotalBuy": SensorStateClass.TOTAL,
    "TotalSell": SensorStateClass.TOTAL,
    "Daily": SensorStateClass.TOTAL_INCREASING,
}


def get_device_class(key: str) -> SensorDeviceClass | None:
    """Determine device class from sensor key."""
    for pattern, device_class in DEVICE_CLASS_MAP.items():
        if pattern in key:
            return device_class
    return None


def get_state_class(key: str) -> SensorStateClass | None:
    """Determine state class from sensor key."""
    # Check specific patterns first
    for pattern, state_class in STATE_CLASS_MAP.items():
        if pattern in key:
            return state_class
    
    # Default to measurement for power/voltage/current sensors (but NOT total power)
    if "Power" in key and "Total" not in key:
        return SensorStateClass.MEASUREMENT
    if any(x in key for x in ["Voltage", "Current", "Frequency", "SOC", "Temperature"]):
        return SensorStateClass.MEASUREMENT
    
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Deye Cloud Control sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # Add station sensors
    for station_id in coordinator.stations:
        station_data = coordinator.data.get("stations", {}).get(station_id, {})
        station_latest = station_data.get("data", {})
        
        # Create sensors for all station data points
        for key, value in station_latest.items():
            if key in ["code", "msg", "success", "requestId", "lastUpdateTime"]:
                continue  # Skip metadata fields
                
            entities.append(
                DeyeCloudStationSensor(
                    coordinator=coordinator,
                    station_id=station_id,
                    sensor_key=key,
                )
            )

    # Add device sensors - dynamically create for all available data points
    for device_sn in coordinator.devices:
        device_data = coordinator.data.get("devices", {}).get(device_sn, {})
        data_points = device_data.get("data", {})
        
        # Create a sensor for each data point
        for key, value in data_points.items():
            if not key:  # Skip None keys
                continue
                
            entities.append(
                DeyeCloudDeviceSensor(
                    coordinator=coordinator,
                    device_sn=device_sn,
                    sensor_key=key,
                )
            )

    async_add_entities(entities)


class DeyeCloudStationSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Deye Cloud Station Sensor."""

    def __init__(
        self,
        coordinator,
        station_id: str,
        sensor_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._sensor_key = sensor_key
        
        # Create friendly name from key
        name = sensor_key.replace("_", " ").title()
        self._attr_name = f"{self._get_station_name()} {name}"
        self._attr_unique_id = f"{station_id}_{sensor_key}"
        
        # Auto-detect device class and state class
        self._attr_device_class = get_device_class(sensor_key)
        self._attr_state_class = get_state_class(sensor_key)
        self._attr_native_unit_of_measurement = self._get_unit_of_measurement()
        self._attr_icon = self._get_icon()

    def _get_unit_of_measurement(self) -> str | None:
        """Return the unit based on the sensor key."""
        key_lower = self._sensor_key.lower()
        
        if "power" in key_lower:
            return UnitOfPower.WATT
        elif "energy" in key_lower:
            return UnitOfEnergy.KILO_WATT_HOUR
        elif "soc" in key_lower:
            return PERCENTAGE
        elif "irradiate" in key_lower:
            return "W/m²"
            
        return None

    def _get_station_name(self) -> str:
        """Get station name."""
        station_data = self.coordinator.data.get("stations", {}).get(self._station_id, {})
        return station_data.get("info", {}).get("name", f"Station {self._station_id}")

    def _get_icon(self) -> str:
        """Get icon based on sensor type."""
        key_lower = self._sensor_key.lower()
        if "power" in key_lower or "generation" in key_lower:
            return "mdi:flash"
        elif "energy" in key_lower:
            return "mdi:lightning-bolt"
        elif "battery" in key_lower or "soc" in key_lower:
            return "mdi:battery"
        elif "grid" in key_lower:
            return "mdi:transmission-tower"
        elif "consumption" in key_lower or "load" in key_lower:
            return "mdi:home-lightning-bolt"
        return "mdi:chart-line"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        station_data = self.coordinator.data.get("stations", {}).get(self._station_id, {})
        data = station_data.get("data", {})
        value = data.get(self._sensor_key)
        
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        station_data = self.coordinator.data.get("stations", {}).get(self._station_id, {})
        info = station_data.get("info", {})
        
        return {
            "identifiers": {(DOMAIN, self._station_id)},
            "name": self._get_station_name(),
            "manufacturer": "Deye",
            "model": "Solar Station",
            "sw_version": info.get("version"),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._station_id in self.coordinator.data.get("stations", {})
        )


class DeyeCloudDeviceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Deye Cloud Device Sensor."""

    def __init__(
        self,
        coordinator,
        device_sn: str,
        sensor_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._sensor_key = sensor_key
        
        # Create friendly name from key - just the sensor name, no device prefix
        name = sensor_key.replace("_", " ").title()
        self._attr_name = f"Deye {name}"
        self._attr_unique_id = f"{device_sn}_{sensor_key}"
        
        # Auto-detect device class and state class
        self._attr_device_class = get_device_class(sensor_key)
        self._attr_state_class = get_state_class(sensor_key)
        self._attr_icon = self._get_icon()

    def _get_device_name(self) -> str:
        """Get device name."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        device_type = device_data.get("info", {}).get("deviceType", "Device")
        return f"{device_type} {self._device_sn}"

    def _get_icon(self) -> str:
        """Get icon based on sensor type."""
        key_lower = self._sensor_key.lower()
        if "power" in key_lower:
            return "mdi:flash"
        elif "energy" in key_lower or "production" in key_lower:
            return "mdi:solar-power"
        elif "battery" in key_lower or "soc" in key_lower or "bms" in key_lower:
            return "mdi:battery"
        elif "grid" in key_lower:
            return "mdi:transmission-tower"
        elif "load" in key_lower or "consumption" in key_lower or "ups" in key_lower:
            return "mdi:home-lightning-bolt"
        elif "voltage" in key_lower:
            return "mdi:sine-wave"
        elif "current" in key_lower:
            return "mdi:current-ac"
        elif "frequency" in key_lower:
            return "mdi:waveform"
        elif "pv" in key_lower or "dc" in key_lower or "solar" in key_lower:
            return "mdi:solar-panel"
        elif "temperature" in key_lower:
            return "mdi:thermometer"
        elif "gen" in key_lower or "generator" in key_lower:
            return "mdi:engine"
        return "mdi:gauge"

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        data = device_data.get("data", {})
        value = data.get(self._sensor_key)
        
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                return str(value)
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit based on the sensor key."""
        key_lower = self._sensor_key.lower()
        
        if "power" in key_lower and "reactive" not in key_lower:
            if "k" in key_lower:
                return UnitOfPower.KILO_WATT
            return UnitOfPower.WATT
        elif "energy" in key_lower or "production" in key_lower or "consumption" in key_lower:
            return UnitOfEnergy.KILO_WATT_HOUR
        elif "voltage" in key_lower:
            return UnitOfElectricPotential.VOLT
        elif "current" in key_lower:
            return UnitOfElectricCurrent.AMPERE
        elif "frequency" in key_lower:
            return UnitOfFrequency.HERTZ
        elif "temperature" in key_lower:
            return UnitOfTemperature.CELSIUS
        elif "soc" in key_lower:
            return PERCENTAGE
        elif "apparentpower" in key_lower:
            return "VA"
            
        return None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        info = device_data.get("info", {})
        
        return {
            "identifiers": {(DOMAIN, self._device_sn)},
            "name": self._get_device_name(),
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
