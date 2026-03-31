"""RAPT.io API client with OAuth2 authentication."""

from __future__ import annotations

import time
from typing import Any

import httpx

BASE_URL = "https://api.rapt.io"
TOKEN_URL = "https://id.rapt.io/connect/token"
CLIENT_ID = "rapt-user"


class RaptAuthError(Exception):
    pass


class RaptApiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class RaptClient:
    """Async HTTP client for the RAPT.io API."""

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._http = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

    async def _ensure_token(self) -> None:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return
        resp = await self._http.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
            },
        )
        if resp.status_code != 200:
            raise RaptAuthError(
                f"Authentication failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expires_at = time.time() + expires_in

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        await self._ensure_token()
        resp = await self._http.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        if resp.status_code != 200:
            raise RaptApiError(resp.status_code, resp.text)
        return resp.json()

    async def _post(self, path: str, params: dict[str, Any] | None = None) -> Any:
        await self._ensure_token()
        resp = await self._http.post(
            path,
            params=params,
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        if resp.status_code != 200:
            raise RaptApiError(resp.status_code, resp.text)
        return resp.json()

    async def _post_json(
        self,
        path: str,
        data: Any,
        params: dict[str, Any] | None = None,
    ) -> Any:
        await self._ensure_token()
        resp = await self._http.post(
            path,
            json=data,
            params=params,
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        if resp.status_code != 200:
            raise RaptApiError(resp.status_code, resp.text)
        return resp.json()

    async def _update_fermentation_chamber(
        self, chamber_id: str, updates: dict[str, Any]
    ) -> bool:
        current = await self.get_fermentation_chamber(chamber_id)
        current.update(updates)
        return await self._post_json(
            "/api/FermentationChambers/UpdateFermentationChamber",
            current,
            {"resetValidationCode": "false"},
        )

    async def close(self) -> None:
        await self._http.aclose()

    # -------------------------------------------------------------------------
    # Bonded Devices
    # -------------------------------------------------------------------------

    async def get_bonded_devices(self) -> list[dict]:
        return await self._get("/api/BondedDevices/GetBondedDevices")

    async def get_bonded_device(self, device_id: str) -> dict:
        return await self._get(
            "/api/BondedDevices/GetBondedDevice", {"deviceId": device_id}
        )

    async def get_bonded_device_telemetry(
        self,
        device_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {"deviceId": device_id}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return await self._get("/api/BondedDevices/GetTelemetry", params)

    # -------------------------------------------------------------------------
    # Fermentation Chambers (Gärschrank)
    # -------------------------------------------------------------------------

    async def get_fermentation_chambers(self) -> list[dict]:
        return await self._get(
            "/api/FermentationChambers/GetFermentationChambers"
        )

    async def get_fermentation_chamber(self, chamber_id: str) -> dict:
        return await self._get(
            "/api/FermentationChambers/GetFermentationChamber",
            {"fermentationChamberId": chamber_id},
        )

    async def set_fermentation_chamber_temperature(
        self, chamber_id: str, target: float
    ) -> bool:
        return await self._post(
            "/api/FermentationChambers/SetTargetTemperature",
            {"fermentationChamberId": chamber_id, "target": target},
        )

    async def set_fermentation_chamber_pid_enabled(
        self, chamber_id: str, enabled: bool
    ) -> bool:
        return await self._post(
            "/api/FermentationChambers/SetPIDEnabled",
            {"fermentationChamberId": chamber_id, "state": enabled},
        )

    async def set_fermentation_chamber_pid(
        self, chamber_id: str, p: float, i: float, d: float
    ) -> bool:
        return await self._post(
            "/api/FermentationChambers/SetPID",
            {"fermentationChamberId": chamber_id, "p": p, "i": i, "d": d},
        )

    async def set_fermentation_chamber_heating_enabled(
        self, chamber_id: str, enabled: bool
    ) -> bool:
        return await self._update_fermentation_chamber(
            chamber_id, {"heatingEnabled": enabled}
        )

    async def set_fermentation_chamber_cooling_enabled(
        self, chamber_id: str, enabled: bool
    ) -> bool:
        return await self._update_fermentation_chamber(
            chamber_id, {"coolingEnabled": enabled}
        )

    async def set_fermentation_chamber_fan_enabled(
        self, chamber_id: str, enabled: bool
    ) -> bool:
        return await self._update_fermentation_chamber(
            chamber_id, {"fanEnabled": enabled}
        )

    async def set_fermentation_chamber_light_enabled(
        self, chamber_id: str, state: str
    ) -> bool:
        return await self._update_fermentation_chamber(
            chamber_id, {"lightEnabled": state}
        )

    async def set_fermentation_chamber_cooling_hysteresis(
        self, chamber_id: str, value: float
    ) -> bool:
        return await self._update_fermentation_chamber(
            chamber_id, {"coolingHysteresis": value}
        )

    async def set_fermentation_chamber_heating_hysteresis(
        self, chamber_id: str, value: float
    ) -> bool:
        return await self._update_fermentation_chamber(
            chamber_id, {"heatingHysteresis": value}
        )

    async def set_fermentation_chamber_compressor_delay(
        self, chamber_id: str, minutes: int
    ) -> bool:
        return await self._update_fermentation_chamber(
            chamber_id, {"compressorDelay": minutes}
        )

    async def set_fermentation_chamber_mode_switch_delay(
        self, chamber_id: str, minutes: int
    ) -> bool:
        return await self._update_fermentation_chamber(
            chamber_id, {"modeSwitchDelay": minutes}
        )

    async def get_fermentation_chamber_telemetry(
        self,
        chamber_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        profile_session_id: str | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {"fermentationChamberId": chamber_id}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if profile_session_id:
            params["profileSessionId"] = profile_session_id
        return await self._get(
            "/api/FermentationChambers/GetTelemetry", params
        )

    # -------------------------------------------------------------------------
    # Hydrometers (RaptPill)
    # -------------------------------------------------------------------------

    async def get_hydrometers(self) -> list[dict]:
        return await self._get("/api/Hydrometers/GetHydrometers")

    async def get_hydrometer(self, hydrometer_id: str) -> dict:
        return await self._get(
            "/api/Hydrometers/GetHydrometer",
            {"hydrometerId": hydrometer_id},
        )

    async def get_hydrometer_telemetry(
        self,
        hydrometer_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        profile_session_id: str | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {"hydrometerId": hydrometer_id}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if profile_session_id:
            params["profileSessionId"] = profile_session_id
        return await self._get("/api/Hydrometers/GetTelemetry", params)

    # -------------------------------------------------------------------------
    # Profiles
    # -------------------------------------------------------------------------

    async def get_profiles(self) -> list[dict]:
        return await self._get("/api/Profiles/GetProfiles")

    async def get_profile(self, profile_id: str) -> dict:
        return await self._get(
            "/api/Profiles/GetProfile", {"profileId": profile_id}
        )

    async def get_profile_types(self) -> list[dict]:
        return await self._get("/api/ProfileTypes/GetAll")
