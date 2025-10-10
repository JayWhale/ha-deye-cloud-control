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

# Sensor definitions: (key, name, unit, device_class, state_class, icon)
STATION_SENSORS = [
    ("todayEnergy", "Today Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "mdi:solar-power"),
    ("totalEnergy", "Total Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL, "mdi:solar-power"),
    ("currentPower", "Current Power", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:flash"),
    ("gridPower", "Grid Power", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:transmission-tower"),
    ("buyPower", "Buy Power", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:transmission-tower-import"),
    ("sellPower", "Sell Power", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:transmission-tower-export"),
]

DEVICE_SENSORS = [
    ("pac", "AC Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:flash"),
    ("dailyEnergy", "Daily Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, "mdi:solar-power"),
    ("totalEnergy", "Total Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL, "mdi:solar-power"),
    
    # Battery sensors
    ("batteryPower", "Battery Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:battery"),
    ("batterySoc", "Battery SOC", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, "mdi:battery"),
    ("batteryVoltage", "Battery Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:battery"),
    ("batteryCurrent", "Battery Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "mdi:battery"),
    ("batteryTemperature", "Battery Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "mdi:thermometer"),
    
    # Grid sensors
    ("gridVoltage", "Grid Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:sine-wave"),
    ("gridCurrent", "Grid Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "mdi:current-ac"),
    ("gridFrequency", "Grid Frequency", UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, "mdi:sine-wave"),
    ("gridPower", "Grid Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:transmission-tower"),
    
    # Load sensors
    ("loadPower", "Load Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:home-lightning-bolt"),
    ("loadVoltage", "Load Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:home-lightning-bolt"),
    ("loadCurrent", "Load Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "mdi:home-lightning-bolt"),
    
    # PV sensors
    ("pv1Power", "PV1 Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:solar-panel"),
    ("pv1Voltage", "PV1 Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:solar-panel"),
    ("pv1Current", "PV1 Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "mdi:solar-panel"),
    ("pv2Power", "PV2 Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:solar-panel"),
    ("pv2Voltage", "PV2 Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "mdi:solar-panel"),
    ("pv2Current", "PV2 Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "mdi:solar-panel"),
    
    # Inverter sensors
    ("inverterTemperature", "Inverter Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "mdi:thermometer"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Deye Cloud sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # Add station sensors
    for station_id in coordinator.stations:
        for sensor_def in STATION_SENSORS:
            entities.append(
                DeyeCloudStationSensor(
                    coordinator=coordinator,
                    station_id=station_id,
                    sensor_key=sensor_def[0],
                    sensor_name=sensor_def[1],
                    unit=sensor_def[2],
                    device_class=sensor_def[3],
                    state_class=sensor_def[4],
                    icon=sensor_def[5],
                )
            )

    # Add device sensors
    for device_sn in coordinator.devices:
        for sensor_def in DEVICE_SENSORS:
            entities.append(
                DeyeCloudDeviceSensor(
                    coordinator=coordinator,
                    device_sn=device_sn,
                    sensor_key=sensor_def[0],
                    sensor_name=sensor_def[1],
                    unit=sensor_def[2],
                    device_class=sensor_def[3],
                    state_class=sensor_def[4],
                    icon=sensor_def[5],
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
        sensor_name: str,
        unit: str,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._sensor_key = sensor_key
        self._attr_name = f"{self._get_station_name()} {sensor_name}"
        self._attr_unique_id = f"{station_id}_{sensor_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon

    def _get_station_name(self) -> str:
        """Get station name."""
        station_data = self.coordinator.data.get("stations", {}).get(self._station_id, {})
        return station_data.get("info", {}).get("name", f"Station {self._station_id}")

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
        sensor_name: str,
        unit: str,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_sn = device_sn
        self._sensor_key = sensor_key
        self._attr_name = f"{self._get_device_name()} {sensor_name}"
        self._attr_unique_id = f"{device_sn}_{sensor_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon

    def _get_device_name(self) -> str:
        """Get device name."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        return device_data.get("info", {}).get("deviceName", f"Device {self._device_sn}")

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.data.get("devices", {}).get(self._device_sn, {})
        data = device_data.get("data", {})
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
