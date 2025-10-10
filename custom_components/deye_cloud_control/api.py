"""Deye Cloud API Client."""
import asyncio
import logging
import hashlib
import time
from typing import Any, Dict, List, Optional
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

API_TIMEOUT = 30


class DeyeCloudApiError(Exception):
    """Base exception for Deye Cloud API errors."""


class DeyeCloudAuthError(DeyeCloudApiError):
    """Authentication error."""


class DeyeCloudClient:
    """Client to interact with Deye Cloud API."""

    def __init__(
        self,
        base_url: str,
        app_id: str,
        app_secret: str,
        email: str,
        password: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialize the client."""
        self.base_url = base_url
        self.app_id = app_id
        self.app_secret = app_secret
        self.email = email
        self.password_hash = hashlib.sha256(password.encode()).hexdigest().lower()
        self._session = session
        self._close_session = False
        self._access_token: Optional[str] = None
        self._token_expiry: int = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True
        return self._session

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

        # Add access token if required and available
        if require_auth:
            if not self._access_token or time.time() >= self._token_expiry:
                await self.obtain_token()
            data["access_token"] = self._access_token

        headers = {
            "Content-Type": "application/json",
        }

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

            # Check API response code (0 and 1000000 are success codes)
            # Handle both string and integer codes
            code = result.get("code")
            if code not in [0, 1000000, "0", "1000000"]:
                error_msg = result.get("msg", "Unknown error")
                _LOGGER.error("API error: %s (code: %s)", error_msg, code)
                if code in [1001, 1002, 1003, "1001", "1002", "1003"]:  # Auth errors
                    raise DeyeCloudAuthError(error_msg)
                raise DeyeCloudApiError(error_msg)

            return result.get("data", {})

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise DeyeCloudApiError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error("Request timeout")
            raise DeyeCloudApiError("Request timeout") from err

    async def obtain_token(self) -> str:
        """Obtain access token."""
        _LOGGER.debug("Obtaining new access token")
        
        # Token endpoint requires appId as query parameter
        url = f"{self.base_url}/account/token?appId={self.app_id}"
        
        request_data = {
            "appSecret": self.app_secret,
            "email": self.email,
            "password": self.password_hash,
        }

        session = await self._get_session()
        
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                async with session.post(
                    url,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

            _LOGGER.debug("Token response: code=%s (type=%s), msg=%s", 
                         result.get("code"), type(result.get("code")), result.get("msg"))

            # Check for success (Deye uses both 0 and 1000000 as success codes)
            # Handle both string and integer codes
            code = result.get("code")
            if code not in [0, 1000000, "0", "1000000"]:
                error_msg = result.get("msg", "Unknown error")
                _LOGGER.error("Token request failed: %s (code: %s)", error_msg, code)
                raise DeyeCloudAuthError(f"{error_msg} (code: {code})")

            data = result.get("data", {})
            self._access_token = data.get("access_token")
            
            if not self._access_token:
                _LOGGER.error("No access token in response data: %s", data)
                raise DeyeCloudAuthError("Failed to obtain access token - no token in response")
            
            # Token expires after 60 days according to docs
            expires_in = 60 * 24 * 60 * 60  # 60 days in seconds
            self._token_expiry = time.time() + expires_in - 86400  # Refresh 1 day early
            
            _LOGGER.debug("Access token obtained successfully, expires in %d days", expires_in // 86400)
            return self._access_token

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during token request: %s", err)
            raise DeyeCloudApiError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout during token request")
            raise DeyeCloudApiError("Request timeout") from err

    async def get_station_list(self) -> List[Dict[str, Any]]:
        """Get list of stations."""
        result = await self._request("POST", "/station/list")
        return result.get("stationList", [])

    async def get_station_list_with_devices(self) -> List[Dict[str, Any]]:
        """Get list of stations with their devices."""
        result = await self._request("POST", "/station/listWithDevice")
        return result.get("stationList", [])

    async def get_device_list(self) -> List[Dict[str, Any]]:
        """Get list of devices."""
        result = await self._request("POST", "/device/list")
        return result.get("deviceList", [])

    async def get_device_latest_data(self, device_sns: List[str]) -> Dict[str, Any]:
        """Get latest data for devices (up to 10 at once)."""
        if len(device_sns) > 10:
            raise ValueError("Maximum 10 devices per request")
        
        data = {"deviceSnList": device_sns}
        result = await self._request("POST", "/device/latest", data=data)
        return result

    async def get_station_latest_data(self, station_id: str) -> Dict[str, Any]:
        """Get latest data for a station."""
        data = {"stationId": station_id}
        result = await self._request("POST", "/station/latest", data=data)
        return result

    async def get_device_measure_points(self, device_sn: str) -> List[str]:
        """Get available measure points for a device."""
        data = {"deviceSn": device_sn}
        result = await self._request("POST", "/device/measurePoints", data=data)
        return result.get("measurePoints", [])

    async def get_device_history(
        self,
        device_sn: str,
        start_time: int,
        end_time: int,
        time_type: str = "day",
    ) -> Dict[str, Any]:
        """Get device history data.
        
        Args:
            device_sn: Device serial number
            start_time: Start timestamp (10-digit Unix timestamp in seconds)
            end_time: End timestamp (10-digit Unix timestamp in seconds)
            time_type: 'day', 'month', or 'year'
        """
        data = {
            "deviceSn": device_sn,
            "startTime": start_time,
            "endTime": end_time,
            "timeType": time_type,
        }
        result = await self._request("POST", "/device/history", data=data)
        return result

    async def get_battery_config(self, device_sn: str) -> Dict[str, Any]:
        """Get battery configuration."""
        data = {"deviceSn": device_sn}
        result = await self._request("POST", "/config/battery", data=data)
        return result

    async def get_system_config(self, device_sn: str) -> Dict[str, Any]:
        """Get system configuration."""
        data = {"deviceSn": device_sn}
        result = await self._request("POST", "/config/system", data=data)
        return result

    async def set_battery_mode(
        self, device_sn: str, charge_mode: bool
    ) -> Dict[str, Any]:
        """Enable or disable battery charge mode."""
        data = {"deviceSn": device_sn, "chargeMode": charge_mode}
        result = await self._request("POST", "/order/battery/modeControl", data=data)
        return result

    async def set_work_mode(
        self, device_sn: str, work_mode: str
    ) -> Dict[str, Any]:
        """Set system work mode.
        
        Args:
            device_sn: Device serial number
            work_mode: 'SELLING_FIRST', 'ZERO_EXPORT_TO_LOAD', or 'ZERO_EXPORT_TO_CT'
        """
        data = {"deviceSn": device_sn, "workMode": work_mode}
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
        data = {"deviceSn": device_sn, "energyPattern": energy_pattern}
        result = await self._request("POST", "/order/sys/energyPattern/update", data=data)
        return result

    async def close(self) -> None:
        """Close the client session."""
        if self._close_session and self._session:
            await self._session.close()
            self._session = None

    async def test_connection(self) -> bool:
        """Test if the connection is working."""
        try:
            _LOGGER.debug("Testing connection to Deye Cloud API")
            await self.obtain_token()
            _LOGGER.debug("Connection test successful")
            return True
        except DeyeCloudAuthError as err:
            _LOGGER.error("Authentication failed during connection test: %s", err)
            return False
        except DeyeCloudApiError as err:
            _LOGGER.error("API error during connection test: %s", err)
            return False
        except Exception as err:
            _LOGGER.error("Unexpected error during connection test: %s", err)
            return False
