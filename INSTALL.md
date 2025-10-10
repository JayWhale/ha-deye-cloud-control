# Deye Cloud Control Integration - Installation Guide

## Quick Start

### Step 1: Create Directory Structure

SSH into your Home Assistant instance or use the File Editor add-on, then create the integration folder:

```bash
mkdir -p /config/custom_components/deye_cloud_control
```

### Step 2: Copy Files

Copy all the integration files into the `deye_cloud_control` folder:

```
/config/custom_components/deye_cloud_control/
├── __init__.py
├── api.py
├── config_flow.py
├── const.py
├── manifest.json
├── sensor.py
├── switch.py
├── select.py
└── strings.json
```

**All files have been provided above in separate artifacts.**

### Step 3: Restart Home Assistant

1. Go to **Settings** → **System** → **Restart**
2. Click **Restart Home Assistant**
3. Wait for Home Assistant to restart

### Step 4: Get Your Deye Cloud API Credentials

1. Go to [https://developer.deyecloud.com/app](https://developer.deyecloud.com/app)
2. Log in with your Deye Cloud account
3. Create a new application (if you haven't already)
4. Copy your **App ID** and **App Secret**

### Step 5: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Deye Cloud Control"
4. Enter your credentials:
   - **App ID**: Your application ID from the developer portal
   - **App Secret**: Your application secret from the developer portal
   - **Update Interval**: How often to fetch data (default: 60 seconds)
5. Click **Submit**

### Step 6: Verify Installation

1. Go to **Settings** → **Devices & Services** → **Deye Cloud Control**
2. You should see your stations and devices listed
3. Click on a device to see all available entities
4. Check **Settings** → **Devices & Services** → **Entities** and search for "deye" to see all sensors

## File Contents

Below are all the files you need to create. Copy each one exactly as shown:

### 1. manifest.json
```json
{
  "domain": "deye_cloud",
  "name": "Deye Cloud",
  "codeowners": ["@yourusername"],
  "config_flow": true,
  "documentation": "https://github.com/yourusername/deye_cloud",
  "integration_type": "hub",
  "iot_class": "cloud_polling",
  "requirements": ["aiohttp>=3.8.0"],
  "version": "1.0.0"
}
```

### 2. const.py
See the "Deye Cloud Constants" artifact above.

### 3. api.py
See the "Deye Cloud API Client" artifact above.

### 4. __init__.py
See the "Deye Cloud Init" artifact above.

### 5. config_flow.py
See the "Deye Cloud Config Flow" artifact above.

### 6. sensor.py
See the "Deye Cloud Sensors" artifact above.

### 7. switch.py
See the "Deye Cloud Switches" artifact above.

### 8. select.py
See the "Deye Cloud Selects" artifact above.

### 9. strings.json
See the "Deye Cloud Translations" artifact above.

## Troubleshooting Installation

### Integration Doesn't Appear

If "Deye Cloud Control" doesn't appear in the integration list:

1. Check that all files are in the correct location
2. Verify file permissions (files should be readable)
3. Check Home Assistant logs for errors:
   - **Settings** → **System** → **Logs**
   - Look for errors mentioning "deye_cloud_control"
4. Make sure you restarted Home Assistant after copying files
5. Try clearing your browser cache (Ctrl+F5)

### Python Errors

If you see Python errors in the logs:

1. Verify all files were copied completely (no truncation)
2. Check for proper indentation (Python is sensitive to this)
3. Ensure you're running a recent version of Home Assistant (2023.x or newer)

### Import Errors

If you see import errors:
- The integration automatically installs `aiohttp>=3.8.0`
- Restart Home Assistant again after the first failed attempt
- Check your internet connection for downloading dependencies

## Testing the Integration

### 1. Check Logs

After adding the integration, check logs for any errors:

```
Settings → System → Logs
```

Look for entries with "deye_cloud" - there should be debug messages about token acquisition and data fetching.

### 2. Verify Sensors

Go to **Developer Tools** → **States** and search for entities starting with:
- `sensor.` (your device/station sensors)
- `switch.` (battery charge mode)
- `select.` (work mode, energy pattern)

### 3. Test Controls

Try toggling the battery charge mode switch or changing the work mode to ensure commands work.

### 4. Check Update Frequency

Watch a sensor value and verify it updates according to your configured interval.

## Advanced Configuration

### Custom Scan Interval

You can change the update interval after setup:

1. Go to **Settings** → **Devices & Services**
2. Click on **Deye Cloud**
3. Click **Configure**
4. Adjust the scan interval
5. Click **Submit**

### Multiple Accounts

To add multiple Deye Cloud accounts:
- Each account uses a different App ID
- Simply add the integration again with different credentials
- Each integration instance will be separate

### Debugging

To enable debug logging for the integration:

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.deye_cloud_control: debug
```

Then restart Home Assistant and check the logs for detailed information.

## Updating the Integration

When updates are available:

1. Download the new files
2. Replace the files in `/config/custom_components/deye_cloud_control/`
3. Restart Home Assistant
4. Check logs for any migration messages

## Uninstalling

To remove the integration:

1. Go to **Settings** → **Devices & Services**
2. Click on **Deye Cloud Control**
3. Click the three dots menu
4. Select **Delete**
5. Optionally, remove the `/config/custom_components/deye_cloud_control/` folder
6. Restart Home Assistant

## Getting Help

If you encounter issues:

1. **Check the logs** - Most issues are explained in the logs
2. **Verify API credentials** - Ensure they're correct in the developer portal
3. **Test API directly** - Use the sample code from Deye's GitHub to verify your credentials work
4. **Check the README** - Review the main README.md for common issues
5. **Create an issue** - If all else fails, create a GitHub issue with:
   - Home Assistant version
   - Integration version
   - Relevant log entries
   - Steps to reproduce the problem

## API Credentials Setup

### Detailed Steps for Developer Portal:

1. Visit [https://developer.deyecloud.com](https://developer.deyecloud.com)
2. Click **Sign In** (or **Sign Up** if you don't have an account)
3. Log in with your Deye Cloud credentials
4. Go to **Application** in the menu
5. Click **Create Application**
6. Fill in:
   - **Application Name**: "Home Assistant" (or any name you prefer)
   - **Description**: "Home Assistant Integration"
7. Click **Submit**
8. Your **App ID** and **App Secret** will be displayed
9. **Important**: Save these credentials securely - you'll need them for setup

## What Gets Created

After successful setup, the integration will create:

### Devices
- One device per station (if you have stations)
- One device per inverter/logger

### Entities (per device, as available)
- ~30+ sensors for monitoring
- 1 switch for battery control
- 2 selects for mode control

### Services
The integration uses standard Home Assistant services:
- `switch.turn_on` / `switch.turn_off` for battery mode
- `select.select_option` for work mode and energy pattern

## Performance Notes

- Default update interval: 60 seconds
- Minimum recommended interval: 30 seconds
- Each update makes 2-3 API calls (tokens, stations, devices)
- API has rate limits (exact limits not publicly documented)
- Use longer intervals if you have many devices

## Next Steps

After installation:
1. Add sensors to your dashboard
2. Set up the Energy Dashboard integration
3. Create automations based on solar production
4. Monitor your system in real-time!

Enjoy your Deye Cloud integration! 🌞🔋
