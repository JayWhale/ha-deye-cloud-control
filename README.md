# Deye Cloud Control - Home Assistant Integration

A custom Home Assistant integration for Deye Cloud solar inverters with full control capabilities.

## Features

- 📊 Real-time monitoring of solar production, battery status, and grid consumption
- 🔋 Battery charge mode control
- ⚙️ Work mode selection (Selling First, Zero Export to Load, Zero Export to CT)
- 🔌 Energy pattern configuration (Battery First, Load First)
- 📈 Comprehensive sensor data including:
  - Solar power generation (current and historical)
  - Battery state of charge, voltage, current, and temperature
  - Grid import/export power
  - Load consumption
  - PV string data (voltage, current, power)
  - Inverter temperature
- 🏠 Multi-station and multi-device support
- ☁️ Cloud-based API integration (no local network access required)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Download this repository
2. Copy the `custom_components/deye_cloud_control` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

### Prerequisites

Before setting up the integration, you need to:

1. Create a Deye Cloud account at [https://www.deyecloud.com](https://www.deyecloud.com)
2. Note which datacenter/region you selected during registration:
   - **Europe, EMEA, Asia-Pacific** → Select "EU" region
   - **Americas** → Select "US" region
3. Register your inverter/logger with your Deye Cloud account
4. Create an application in the [Deye Cloud Developer Portal](https://developer.deyecloud.com/app)
5. Note down your **App ID** and **App Secret**

### Setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Deye Cloud Control"
3. Fill in the configuration:
   - **Region**: Select your datacenter (EU or US)
   - **App ID**: Your application ID from the developer portal
   - **App Secret**: Your application secret from the developer portal
   - **Email**: Your Deye Cloud account email
   - **Password**: Your Deye Cloud account password
   - **Update Interval**: How often to fetch data (default: 60 seconds, minimum: 30)
4. Click **Submit**

The integration will automatically discover all stations and devices associated with your account.

## Entities

### Sensors

The integration creates sensors for each station and device:

#### Station Sensors
- Today Energy (kWh)
- Total Energy (kWh)
- Current Power (kW)
- Grid Power (kW)
- Buy Power (kW)
- Sell Power (kW)

#### Device Sensors
- AC Power (W)
- Daily Energy (kWh)
- Total Energy (kWh)
- Battery Power (W)
- Battery SOC (%)
- Battery Voltage (V)
- Battery Current (A)
- Battery Temperature (°C)
- Grid Voltage (V)
- Grid Current (A)
- Grid Frequency (Hz)
- Grid Power (W)
- Load Power (W)
- Load Voltage (V)
- Load Current (A)
- PV1/PV2 Power (W)
- PV1/PV2 Voltage (V)
- PV1/PV2 Current (A)
- Inverter Temperature (°C)

*Note: Not all sensors may be available for all devices. The integration only creates sensors for data points that your specific device reports.*

### Controls

#### Switches
- **Battery Charge Mode**: Enable/disable battery charging

#### Selects
- **Work Mode**: Choose between:
  - Selling First
  - Zero Export to Load
  - Zero Export to CT
- **Energy Pattern**: Choose between:
  - Battery First
  - Load First

## Usage Examples

### Automations

**Example 1: Charge battery during cheap electricity rates**

```yaml
automation:
  - alias: "Charge Battery During Off-Peak"
    trigger:
      - platform: time
        at: "00:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.my_inverter_battery_charge_mode
```

**Example 2: Switch to battery first mode at night**

```yaml
automation:
  - alias: "Battery First at Night"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: select.select_option
        target:
          entity_id: select.my_inverter_energy_pattern
        data:
          option: "BATTERY_FIRST"
```

### Energy Dashboard

All energy sensors are compatible with Home Assistant's Energy Dashboard. Add them under:
- **Solar Production**: Use "Daily Energy" or "Total Energy" sensors
- **Grid Consumption**: Use "Buy Power" sensors
- **Return to Grid**: Use "Sell Power" sensors
- **Battery**: Use "Battery SOC" and "Battery Power" sensors

## Troubleshooting

### Authentication Errors

If you see "Invalid credentials":
1. Verify your **email and password** work in the Deye Cloud mobile app or website
2. Check your **App ID and App Secret** in the [Developer Portal](https://developer.deyecloud.com/app)
3. Ensure you selected the correct **region** (EU vs US)
4. Make sure your application status is **"Open"** in the developer portal
5. Check Home Assistant logs for detailed error messages

### Connection Errors

If the integration fails to connect:
1. Check your internet connection
2. Verify the Deye Cloud service is operational
3. Try increasing the update interval to reduce API load
4. Check Home Assistant logs for detailed error messages

### Missing Sensors

If some sensors don't appear:
- Your device may not support all sensor types
- Check the Deye Cloud app to see what data your device reports
- Wait for the next update cycle (based on your scan interval)

### API Rate Limiting

The Deye Cloud API may have rate limits. If you experience issues:
- Increase the update interval in the integration options
- Reduce the number of simultaneous requests

## File Structure

```
custom_components/deye_cloud_control/
├── __init__.py          # Integration setup and coordinator
├── api.py               # Deye Cloud API client
├── config_flow.py       # Configuration flow
├── const.py             # Constants and configuration
├── manifest.json        # Integration manifest
├── sensor.py            # Sensor platform
├── switch.py            # Switch platform
├── select.py            # Select platform
└── strings.json         # Translations
```

## API Documentation

For more information about the Deye Cloud API:
- [API Documentation](https://developer.deyecloud.com/api)
- [Developer Portal](https://developer.deyecloud.com/app)
- [Sample Code Repository](https://github.com/DeyeCloudDevelopers/deye-openapi-client-sample-code)

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/yourusername/deye_cloud_control/issues) page.

For questions about the Deye Cloud API itself, contact: cloudservice@deye.com.cn

## License

This integration is provided as-is under the MIT License.

## Disclaimer

This is a custom integration and is not officially supported by Deye. Use at your own risk.
