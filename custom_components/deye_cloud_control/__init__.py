"""The Deye Cloud Control integration."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DeyeCloudApiError, DeyeCloudClient
from .const import (
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REGION,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    REGIONS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Deye Cloud from a config entry."""
    region = entry.data[CONF_REGION]
    base_url = REGIONS[region]["base_url"]
    app_id = entry.data[CONF_APP_ID]
    app_secret = entry.data[CONF_APP_SECRET]
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    client = DeyeCloudClient(
        base_url=base_url,
        app_id=app_id,
        app_secret=app_secret,
        email=email,
        password=password,
    )

    # Test connection
    try:
        await client.obtain_token()
    except DeyeCloudApiError as err:
        await client.close()
        raise ConfigEntryNotReady(f"Unable to connect to Deye Cloud: {err}") from err

    coordinator = DeyeCloudDataUpdateCoordinator(
        hass,
        client=client,
        update_interval=timedelta(seconds=scan_interval),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Setup options update listener
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
        await coordinator.client.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class DeyeCloudDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Deye Cloud data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: DeyeCloudClient,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.client = client
        self.stations = []
        self.devices = []

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            # Get stations with devices
            _LOGGER.debug("Fetching station list with devices")
            stations_data = await self.client.get_station_list_with_devices()
            _LOGGER.debug("Raw stations response: %s", stations_data)
            _LOGGER.debug("Received %d stations", len(stations_data) if isinstance(stations_data, list) else 0)
            
            data = {
                "stations": {},
                "devices": {},
            }

            # Process each station
            for station in stations_data:
                station_id = station.get("id")
                if not station_id:
                    continue

                _LOGGER.debug("Processing station: %s (ID: %s)", station.get("name"), station_id)

                # Get station latest data
                try:
                    station_latest = await self.client.get_station_latest_data(
                        station_id
                    )
                    data["stations"][station_id] = {
                        "info": station,
                        "data": station_latest,
                    }
                    _LOGGER.debug("Station %s data retrieved successfully", station_id)
                except DeyeCloudApiError as err:
                    _LOGGER.warning(
                        "Failed to get data for station %s: %s", station_id, err
                    )

                # Process devices in this station
                devices = station.get("deviceList", [])
                _LOGGER.debug("Station %s has %d devices", station_id, len(devices))
                device_sns = [dev.get("deviceSn") for dev in devices if dev.get("deviceSn")]
                
                # Fetch device data in batches of 10
                for i in range(0, len(device_sns), 10):
                    batch = device_sns[i:i+10]
                    _LOGGER.debug("Fetching data for device batch: %s", batch)
                    try:
                        device_data = await self.client.get_device_latest_data(batch)
                        _LOGGER.debug("Device data response: %s", device_data)
                        
                        # Store device data
                        for dev in devices:
                            dev_sn = dev.get("deviceSn")
                            if dev_sn in device_data:
                                data["devices"][dev_sn] = {
                                    "info": dev,
                                    "data": device_data[dev_sn],
                                }
                                _LOGGER.debug("Stored data for device %s", dev_sn)
                    except DeyeCloudApiError as err:
                        _LOGGER.warning(
                            "Failed to get data for devices %s: %s", batch, err
                        )

            self.stations = list(data["stations"].keys())
            self.devices = list(data["devices"].keys())
            
            _LOGGER.info("Update complete: %d stations, %d devices", 
                        len(self.stations), len(self.devices))

            return data

        except DeyeCloudApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
