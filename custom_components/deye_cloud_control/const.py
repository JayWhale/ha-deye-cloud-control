"""Constants for the Deye Cloud Control integration."""
from homeassistant.const import Platform

DOMAIN = "deye_cloud_control"

# Config
CONF_APP_ID = "app_id"
CONF_APP_SECRET = "app_secret"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_REGION = "region"

# Defaults
DEFAULT_SCAN_INTERVAL = 60  # seconds

# Regions
REGION_EU = "eu"
REGION_US = "us"

REGIONS = {
    REGION_EU: {
        "name": "Europe, EMEA, Asia-Pacific",
        "base_url": "https://eu1-developer.deyecloud.com/v1.0",
    },
    REGION_US: {
        "name": "Americas",
        "base_url": "https://us1-developer.deyecloud.com/v1.0",
    },
}

# Platforms
PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.SELECT]

# Coordinator
COORDINATOR = "coordinator"

# Device classes and units
ATTR_POWER = "power"
ATTR_ENERGY = "energy"
ATTR_VOLTAGE = "voltage"
ATTR_CURRENT = "current"
ATTR_FREQUENCY = "frequency"
ATTR_TEMPERATURE = "temperature"
ATTR_BATTERY_SOC = "battery_soc"
ATTR_BATTERY_POWER = "battery_power"
ATTR_GRID_POWER = "grid_power"
ATTR_LOAD_POWER = "load_power"
ATTR_PV_POWER = "pv_power"

# Work modes
WORK_MODE_SELLING_FIRST = "SELLING_FIRST"
WORK_MODE_ZERO_EXPORT_TO_LOAD = "ZERO_EXPORT_TO_LOAD"
WORK_MODE_ZERO_EXPORT_TO_CT = "ZERO_EXPORT_TO_CT"

WORK_MODES = [
    WORK_MODE_SELLING_FIRST,
    WORK_MODE_ZERO_EXPORT_TO_LOAD,
    WORK_MODE_ZERO_EXPORT_TO_CT,
]

# Energy patterns
ENERGY_PATTERN_BATTERY_FIRST = "BATTERY_FIRST"
ENERGY_PATTERN_LOAD_FIRST = "LOAD_FIRST"

ENERGY_PATTERNS = [
    ENERGY_PATTERN_BATTERY_FIRST,
    ENERGY_PATTERN_LOAD_FIRST,
]
