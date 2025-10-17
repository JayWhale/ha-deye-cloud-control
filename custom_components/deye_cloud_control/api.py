"""API client for Deye Cloud."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

API_TIMEOUT = 30
TOKEN_EXPIRY_BUFFER = 300  # Refresh token 5 minutes before expiry


class DeyeCloudApiError(Exception):
    """Base exception for Deye Cloud API errors."""
    pass


class DeyeCloudAuthError(DeyeCloudApiError):
    """Authentication error."""
    pass


class DeyeCloudClient:
    """Deye Cloud API client."""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        email: str,
        password: str,
        base_url: str = "https://eu1-developer.deyecloud.com/v1.0",
    ) -> None:
        """Initialize the client."""
        self.app_id = app_id
        self.app_secret = app_secret
        self.email = email
        self.password = password
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def obtain_token(self) -> None:
        """Obtain access token."""
        session = await self._get_session()
        
        # appId goes in the URL as query parameter
        url = f"{self.base_url}/account/token?appId={self.app_id}"

        # Everything else goes in the body
        data = {
            "appSecret": self.app_secret,
            "email": self.email,
            "password": self.password,
        }

        headers = {"Content-Type": "application/json"}

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                async with session.post(url, json=data, headers=headers) as response:
                    response.raise_for_status()
                    result = await response.json()

            code = result.get("code")
            if code not in [0, 1000000, "0", "1000000"]:
                error_msg = result.get("msg", "Unknown error")
                _LOGGER.error("Token error: %s (code: %s)", error_msg, code)
                raise DeyeCloudAuthError(error_msg)

            token_data = result.get("data", {})
            self._access_token = token_data.get("accessToken")
            if not self._access_token:
                _LOGGER.error("No access token in response: %s", result)
                raise DeyeCloudAuthError("No access token in response")
            
            expires_in = token_data.get("expiresIn", 3600)
            self._token_expiry = time.time() + expires_in - TOKEN_EXPIRY_BUFFER

            _LOGGER.info("Successfully obtained access token, expires in %s seconds", expires_in)

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during token request: %s", err)
            raise DeyeCloudApiError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout during token request")
            raise DeyeCloudApiError("Request timeout") from err

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        """Make API request."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        if data is None:
            data = {}

        headers = {
            "Content-Type": "application/json",
        }

        # Add access token if required and available
        if require_auth:
            if not self._access_token or time.time() >= self._token_expiry:
                await self.obtain_token()
            headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                if method.upper() == "GET":
                    async with session.get(
                        url, params=data, headers=headers
                    ) as response:
                        response.raise_for_status()
                        result = await response.json()
                else:
                    async with session.post(
                        url, json=data, headers=headers
                    ) as response:
                        response.raise_for_status()
                        result = await response.json()

            # Check API response code
            code = result.get("code")
            if code not in [0, 1000000, "0", "1000000"]:
                error_msg = result.get("msg", "Unknown error")
                _LOGGER.error("API error: %s (code: %s)", error_msg, code)
                if code in [1001, 1002, 1003, "1001", "1002", "1003", 2101017, "2101017"]:
                    raise DeyeCloudAuthError(error_msg)
                raise DeyeCloudApiError(error_msg)

            return result.get("data", {})

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise DeyeCloudApiError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error("Request timeout for %s", endpoint)
            raise DeyeCloudApiError("Request timeout") from err

    async def get_station_list(self) -> Dict[str, Any]:
        """Get list of stations."""
        result = await self._request("POST", "/station/list", data={})
        return result

    async def get_device_list(self) -> Dict[str, Any]:
        """Get list of devices."""
        result = await self._request("POST", "/device/list", data={})
        return result

    async def get_device_latest_data(
        self, device_sns: list[str]
    ) -> Dict[str, Any]:
        """Get latest data for devices."""
        if len(device_sns) > 10:
            raise ValueError("Maximum 10 devices per request")

        data = {"deviceList": device_sns}
        result = await self._request("POST", "/device/latest", data=data)
        return result

    async def get_system_config(self, device_sn: str) -> Dict[str, Any]:
        """Get system configuration."""
        data = {"deviceSn": device_sn}
        result = await self._request("POST", "/config/system", data=data)
        return result

    async def get_battery_config(self, device_sn: str) -> Dict[str, Any]:
        """Get battery configuration."""
        data = {"deviceSn": device_sn}
        result = await self._request("POST", "/config/battery", data=data)
        return result

    async def get_tou_config(self, device_sn: str) -> Dict[str, Any]:
        """Get Time of Use configuration."""
        data = {"deviceSn": device_sn}
        result = await self._request("POST", "/config/tou", data=data)
        return result

    # Control methods - FIXED based on API documentation

    async def set_solar_sell(
        self, device_sn: str, enabled: bool
    ) -> Dict[str, Any]:
        """Enable or disable solar sell.
        
        Args:
            device_sn: Device serial number
            enabled: True to enable, False to disable
        """
        data = {
            "action": "on" if enabled else "off",
            "deviceSn": device_sn,
        }
        result = await self._request("POST", "/order/sys/solarSell/control", data=data)
        return result

    async def set_work_mode(
        self, device_sn: str, work_mode: str
    ) -> Dict[str, Any]:
        """Set system work mode.
        
        Args:
            device_sn: Device serial number
            work_mode: 'SELLING_FIRST', 'ZERO_EXPORT_TO_LOAD', or 'ZERO_EXPORT_TO_CT'
        """
        data = {
            "deviceSn": device_sn,
            "workMode": work_mode,
        }
        result = await self._request("POST", "/order/sys/workMode/update", data=data)
        return result

    async def set_energy_pattern(
        self, device_sn: str, energy_pattern: str
    ) -> Dict[str, Any]:
        """Set energy pattern.
        
        Args:
            device_sn: Device serial number
            energy_pattern: 'BATTERY_FIRST' or 'LOAD_FIRST'
        """
        data = {
            "deviceSn": device_sn,
            "energyPattern": energy_pattern,
        }
        result = await self._request("POST", "/order/sys/energyPattern/update", data=data)
        return result

    async def set_max_sell_power(
        self, device_sn: str, power: int
    ) -> Dict[str, Any]:
        """Set max sell power.
        
        Args:
            device_sn: Device serial number
            power: Max sell power in watts
        """
        data = {
            "deviceSn": device_sn,
            "powerType": "MAX_SELL_POWER",
            "value": power,
        }
        result = await self._request("POST", "/order/sys/power/update", data=data)
        return result

    async def set_battery_charge_current(
        self, device_sn: str, current: int
    ) -> Dict[str, Any]:
        """Set battery charge current limit.
        
        Args:
            device_sn: Device serial number
            current: Max charge current in amps
        """
        data = {
            "deviceSn": device_sn,
            "parameterType": "MAX_CHARGE_CURRENT",
            "value": current,
        }
        result = await self._request("POST", "/order/battery/parameter/update", data=data)
        return result

    async def set_battery_discharge_current(
        self, device_sn: str, current: int
    ) -> Dict[str, Any]:
        """Set battery discharge current limit.
        
        Args:
            device_sn: Device serial number
            current: Max discharge current in amps
        """
        data = {
            "deviceSn": device_sn,
            "parameterType": "MAX_DISCHARGE_CURRENT",
            "value": current,
        }
        result = await self._request("POST", "/order/battery/parameter/update", data=data)
        return result

    async def set_battery_mode(
        self, device_sn: str, charge_mode: bool
    ) -> Dict[str, Any]:
        """Enable or disable battery charge mode.
        
        NOTE: This endpoint is not shown in the screenshots provided.
        This may not work correctly until we have the actual API documentation.
        """
        data = {
            "deviceSn": device_sn,
            "chargeMode": charge_mode,
        }
        result = await self._request("POST", "/order/battery/modeControl", data=data)
        return result

    async def set_tou_config(
        self, device_sn: str, tou_items: list[dict], timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Set Time of Use configuration.
        
        Args:
            device_sn: Device serial number
            tou_items: List of TOU setting items
            timeout_seconds: Command timeout
        """
        data = {
            "deviceSn": device_sn,
            "timeUseSettingItems": tou_items,
            "timeoutSeconds": timeout_seconds,
        }
        result = await self._request("POST", "/order/sys/tou/update", data=data)
        return result
