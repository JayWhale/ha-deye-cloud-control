"""Deye Cloud API Client."""
import logging
import time
from typing import Any

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

API_TIMEOUT = 30
TOKEN_EXPIRY_BUFFER = 300  # 5 minutes


class DeyeCloudApiError(Exception):
    """Base exception for Deye Cloud API errors."""
    pass


class DeyeCloudAuthError(DeyeCloudApiError):
    """Authentication error."""
    pass


class DeyeCloudApiClient:
    """Deye Cloud API Client."""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        email: str,
        password: str,
        base_url: str,
        session: aiohttp.ClientSession = None,
    ) -> None:
        """Initialize the API client."""
        self.app_id = app_id
        self.app_secret = app_secret
        self.email = email
        self.password = password
        self.base_url = base_url
        self._session = session
        self._access_token = None
        self._token_expiry = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def obtain_token(self) -> None:
        """Obtain access token - THIS IS THE WORKING VERSION FROM OCT 11."""
        session = await self._get_session()
        
        # Use /v1.0/token endpoint with ALL params in body
        url = f"{self.base_url}/v1.0/token"

        # ALL parameters go in the request body
        data = {
            "appId": self.app_id,
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

            # Token comes from the root of the response, not from data
            self._access_token = result.get("accessToken")
            if not self._access_token:
                _LOGGER.error("No access token in response: %s", result)
                raise DeyeCloudAuthError("No access token in response")
            
            expires_in = result.get("expiresIn", 3600)
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
        data: dict[str, Any] = None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        """Make API request with Bearer token in header."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        if data is None:
            data = {}

        # Get fresh token if needed
        if require_auth:
            if not self._access_token or time.time() >= self._token_expiry:
                await self.obtain_token()

        headers = {
            "Content-Type": "application/json",
        }
        
        # Add Bearer token to Authorization header
        if require_auth and self._access_token:
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
                if code in [1001, 1002, 1003, 2101017, "1001", "1002", "1003", "2101017"]:
                    raise DeyeCloudAuthError(error_msg)
                raise DeyeCloudApiError(error_msg)

            return result.get("data", {})

        except aiohttp.ClientError as err:
            _LOGGER.error("API request error: %s", err)
            raise DeyeCloudApiError(f"Request failed: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error("API request timeout")
            raise DeyeCloudApiError("Request timeout") from err

    async def get_station_list(self) -> list[dict[str, Any]]:
        """Get list of stations."""
        result = await self._request("POST", "/v1.0/station/list")
        return result.get("stationList", [])

    async def get_device_list(self, station_id: str) -> list[dict[str, Any]]:
        """Get list of devices for a station."""
        data = {"stationId": station_id}
        result = await self._request("POST", "/v1.0/device/list", data)
        return result.get("deviceList", [])

    async def get_device_info(self, device_sn: str) -> dict[str, Any]:
        """Get device information."""
        data = {"deviceSn": device_sn}
        return await self._request("POST", "/v1.0/device/info", data)

    async def get_realtime_data(self, device_sn: str) -> dict[str, Any]:
        """Get real-time device data."""
        data = {"sn": device_sn}
        return await self._request("POST", "/v1.0/device/getDataInfo", data)

    async def set_work_mode(self, device_sn: str, mode: int) -> None:
        """Set device work mode."""
        data = {
            "deviceSn": device_sn,
            "type": 2,
            "value": mode,
        }
        await self._request("POST", "/v1.0/device/setting", data)

    async def set_solar_sell(self, device_sn: str, enabled: bool) -> None:
        """Enable or disable solar selling."""
        data = {
            "deviceSn": device_sn,
            "type": 14,
            "value": 1 if enabled else 0,
        }
        await self._request("POST", "/v1.0/device/setting", data)

    async def set_max_sell_power(self, device_sn: str, power: int) -> None:
        """Set maximum sell power in watts."""
        data = {
            "deviceSn": device_sn,
            "type": 15,
            "value": power,
        }
        await self._request("POST", "/v1.0/device/setting", data)
