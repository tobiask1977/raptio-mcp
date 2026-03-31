"""RAPT.io MCP Server."""

from __future__ import annotations

import json
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .client import RaptApiError, RaptAuthError, RaptClient

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[Tool] = [
    # --- Bonded Devices ---
    Tool(
        name="get_bonded_devices",
        description="List all devices bonded to the RAPT account (all device types).",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_bonded_device",
        description="Get details for a specific bonded device by UUID.",
        inputSchema={
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "UUID of the device",
                }
            },
            "required": ["device_id"],
        },
    ),
    Tool(
        name="get_bonded_device_telemetry",
        description="Get telemetry data for a bonded device.",
        inputSchema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "UUID of the device"},
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO 8601 format (e.g. 2024-01-01T00:00:00Z)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO 8601 format",
                },
            },
            "required": ["device_id"],
        },
    ),
    # --- Fermentation Chambers (Gärschrank) ---
    Tool(
        name="get_fermentation_chambers",
        description="List all fermentation chambers (Gärschränke) in the RAPT account.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_fermentation_chamber",
        description=(
            "Get detailed status of a single fermentation chamber including "
            "current temperature, target temperature, PID settings, heating/cooling state, "
            "run-time statistics, and active profile."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {
                    "type": "string",
                    "description": "UUID of the fermentation chamber",
                }
            },
            "required": ["chamber_id"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_temperature",
        description=(
            "Set the target temperature for a fermentation chamber. "
            "The value is in the unit configured on the device (°C or °F)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {
                    "type": "string",
                    "description": "UUID of the fermentation chamber",
                },
                "target": {
                    "type": "number",
                    "description": "Target temperature (°C or °F depending on device setting)",
                },
            },
            "required": ["chamber_id", "target"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_pid_enabled",
        description="Enable or disable PID temperature control for a fermentation chamber.",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {
                    "type": "string",
                    "description": "UUID of the fermentation chamber",
                },
                "enabled": {
                    "type": "boolean",
                    "description": "true to enable PID, false to disable",
                },
            },
            "required": ["chamber_id", "enabled"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_pid",
        description=(
            "Configure PID parameters (proportional, integral, derivative) "
            "for a fermentation chamber's temperature controller."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {
                    "type": "string",
                    "description": "UUID of the fermentation chamber",
                },
                "p": {"type": "number", "description": "Proportional gain"},
                "i": {"type": "number", "description": "Integral gain"},
                "d": {"type": "number", "description": "Derivative gain"},
            },
            "required": ["chamber_id", "p", "i", "d"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_heating_enabled",
        description="Enable or disable the heating element of a fermentation chamber.",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {"type": "string", "description": "UUID of the fermentation chamber"},
                "enabled": {"type": "boolean", "description": "true to enable heating, false to disable"},
            },
            "required": ["chamber_id", "enabled"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_cooling_enabled",
        description="Enable or disable the cooling (compressor) of a fermentation chamber.",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {"type": "string", "description": "UUID of the fermentation chamber"},
                "enabled": {"type": "boolean", "description": "true to enable cooling, false to disable"},
            },
            "required": ["chamber_id", "enabled"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_fan_enabled",
        description="Enable or disable the fan of a fermentation chamber.",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {"type": "string", "description": "UUID of the fermentation chamber"},
                "enabled": {"type": "boolean", "description": "true to enable fan, false to disable"},
            },
            "required": ["chamber_id", "enabled"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_light_enabled",
        description="Control the light of a fermentation chamber (On, Off, or Auto).",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {"type": "string", "description": "UUID of the fermentation chamber"},
                "state": {
                    "type": "string",
                    "enum": ["On", "Off", "Auto"],
                    "description": "Light state: On, Off, or Auto",
                },
            },
            "required": ["chamber_id", "state"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_cooling_hysteresis",
        description="Set the cooling hysteresis (deadband) for a fermentation chamber. Valid range: 0.5–10.",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {"type": "string", "description": "UUID of the fermentation chamber"},
                "value": {"type": "number", "description": "Cooling hysteresis value (0.5–10)"},
            },
            "required": ["chamber_id", "value"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_heating_hysteresis",
        description="Set the heating hysteresis (deadband) for a fermentation chamber. Valid range: 0.1–10.",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {"type": "string", "description": "UUID of the fermentation chamber"},
                "value": {"type": "number", "description": "Heating hysteresis value (0.1–10)"},
            },
            "required": ["chamber_id", "value"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_compressor_delay",
        description="Set the compressor restart delay in minutes for a fermentation chamber. Valid range: 2–10.",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {"type": "string", "description": "UUID of the fermentation chamber"},
                "minutes": {"type": "integer", "description": "Compressor delay in minutes (2–10)"},
            },
            "required": ["chamber_id", "minutes"],
        },
    ),
    Tool(
        name="set_fermentation_chamber_mode_switch_delay",
        description="Set the heating/cooling mode switch delay in minutes for a fermentation chamber. Valid range: 2–30.",
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {"type": "string", "description": "UUID of the fermentation chamber"},
                "minutes": {"type": "integer", "description": "Mode switch delay in minutes (2–30)"},
            },
            "required": ["chamber_id", "minutes"],
        },
    ),
    Tool(
        name="get_fermentation_chamber_telemetry",
        description=(
            "Get historical telemetry data for a fermentation chamber, including "
            "temperature readings, compressor/heating run times, and profile progress."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "chamber_id": {
                    "type": "string",
                    "description": "UUID of the fermentation chamber",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO 8601 format (e.g. 2024-01-01T00:00:00Z)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO 8601 format",
                },
                "profile_session_id": {
                    "type": "string",
                    "description": "Optional UUID of a specific profile session to filter by",
                },
            },
            "required": ["chamber_id"],
        },
    ),
    # --- Hydrometers (RaptPill) ---
    Tool(
        name="get_hydrometers",
        description=(
            "List all hydrometers (RaptPill devices) in the RAPT account. "
            "Returns current gravity, temperature, and battery level."
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_hydrometer",
        description=(
            "Get detailed status of a single RaptPill hydrometer including "
            "current gravity (specific gravity), gravity velocity, temperature, and battery level."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "hydrometer_id": {
                    "type": "string",
                    "description": "UUID of the hydrometer/RaptPill",
                }
            },
            "required": ["hydrometer_id"],
        },
    ),
    Tool(
        name="get_hydrometer_telemetry",
        description=(
            "Get historical telemetry data for a RaptPill hydrometer. "
            "Returns timestamped gravity, temperature, and battery readings."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "hydrometer_id": {
                    "type": "string",
                    "description": "UUID of the hydrometer/RaptPill",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO 8601 format (e.g. 2024-01-01T00:00:00Z)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO 8601 format",
                },
                "profile_session_id": {
                    "type": "string",
                    "description": "Optional UUID of a specific profile session to filter by",
                },
            },
            "required": ["hydrometer_id"],
        },
    ),
    # --- Profiles ---
    Tool(
        name="get_profiles",
        description="List all fermentation profiles saved in the RAPT account.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_profile",
        description="Get details of a specific fermentation profile including all steps and alerts.",
        inputSchema={
            "type": "object",
            "properties": {
                "profile_id": {
                    "type": "string",
                    "description": "UUID of the profile",
                }
            },
            "required": ["profile_id"],
        },
    ),
    Tool(
        name="get_profile_types",
        description="List all available profile types in the RAPT system.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _ok(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error: {msg}")]


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


def create_server() -> tuple[Server, RaptClient]:
    username = os.environ.get("RAPT_USERNAME")
    password = os.environ.get("RAPT_PASSWORD")

    if not username or not password:
        raise ValueError(
            "RAPT_USERNAME and RAPT_PASSWORD environment variables must be set."
        )

    client = RaptClient(username=username, password=password)
    server = Server("raptio-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            # Bonded Devices
            if name == "get_bonded_devices":
                return _ok(await client.get_bonded_devices())

            if name == "get_bonded_device":
                return _ok(await client.get_bonded_device(arguments["device_id"]))

            if name == "get_bonded_device_telemetry":
                return _ok(
                    await client.get_bonded_device_telemetry(
                        arguments["device_id"],
                        arguments.get("start_date"),
                        arguments.get("end_date"),
                    )
                )

            # Fermentation Chambers
            if name == "get_fermentation_chambers":
                return _ok(await client.get_fermentation_chambers())

            if name == "get_fermentation_chamber":
                return _ok(
                    await client.get_fermentation_chamber(arguments["chamber_id"])
                )

            if name == "set_fermentation_chamber_temperature":
                result = await client.set_fermentation_chamber_temperature(
                    arguments["chamber_id"], float(arguments["target"])
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_pid_enabled":
                result = await client.set_fermentation_chamber_pid_enabled(
                    arguments["chamber_id"], bool(arguments["enabled"])
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_pid":
                result = await client.set_fermentation_chamber_pid(
                    arguments["chamber_id"],
                    float(arguments["p"]),
                    float(arguments["i"]),
                    float(arguments["d"]),
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_heating_enabled":
                result = await client.set_fermentation_chamber_heating_enabled(
                    arguments["chamber_id"], bool(arguments["enabled"])
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_cooling_enabled":
                result = await client.set_fermentation_chamber_cooling_enabled(
                    arguments["chamber_id"], bool(arguments["enabled"])
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_fan_enabled":
                result = await client.set_fermentation_chamber_fan_enabled(
                    arguments["chamber_id"], bool(arguments["enabled"])
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_light_enabled":
                result = await client.set_fermentation_chamber_light_enabled(
                    arguments["chamber_id"], arguments["state"]
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_cooling_hysteresis":
                result = await client.set_fermentation_chamber_cooling_hysteresis(
                    arguments["chamber_id"], float(arguments["value"])
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_heating_hysteresis":
                result = await client.set_fermentation_chamber_heating_hysteresis(
                    arguments["chamber_id"], float(arguments["value"])
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_compressor_delay":
                result = await client.set_fermentation_chamber_compressor_delay(
                    arguments["chamber_id"], int(arguments["minutes"])
                )
                return _ok({"success": result})

            if name == "set_fermentation_chamber_mode_switch_delay":
                result = await client.set_fermentation_chamber_mode_switch_delay(
                    arguments["chamber_id"], int(arguments["minutes"])
                )
                return _ok({"success": result})

            if name == "get_fermentation_chamber_telemetry":
                return _ok(
                    await client.get_fermentation_chamber_telemetry(
                        arguments["chamber_id"],
                        arguments.get("start_date"),
                        arguments.get("end_date"),
                        arguments.get("profile_session_id"),
                    )
                )

            # Hydrometers
            if name == "get_hydrometers":
                return _ok(await client.get_hydrometers())

            if name == "get_hydrometer":
                return _ok(
                    await client.get_hydrometer(arguments["hydrometer_id"])
                )

            if name == "get_hydrometer_telemetry":
                return _ok(
                    await client.get_hydrometer_telemetry(
                        arguments["hydrometer_id"],
                        arguments.get("start_date"),
                        arguments.get("end_date"),
                        arguments.get("profile_session_id"),
                    )
                )

            # Profiles
            if name == "get_profiles":
                return _ok(await client.get_profiles())

            if name == "get_profile":
                return _ok(await client.get_profile(arguments["profile_id"]))

            if name == "get_profile_types":
                return _ok(await client.get_profile_types())

            return _err(f"Unknown tool: {name}")

        except RaptAuthError as e:
            return _err(f"Authentication failed: {e}")
        except RaptApiError as e:
            return _err(str(e))
        except Exception as e:
            return _err(f"Unexpected error: {e}")

    return server, client


async def _run() -> None:
    server, client = create_server()
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await client.close()


def main() -> None:
    import asyncio

    asyncio.run(_run())


if __name__ == "__main__":
    main()
