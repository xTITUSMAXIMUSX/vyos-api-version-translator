import urllib3
urllib3.disable_warnings()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal

from vyos_service import VyOSDeviceConfig, VyOSDeviceRegistry

# Import routers
from routers.interfaces import ethernet, dummy

app = FastAPI(
    title="VyOS Management API",
    version="1.0.0",
    description="FastAPI backend for managing VyOS devices with version-aware commands",
)


# ============================================================================
# Pydantic Models - Device Management
# ============================================================================


class DeviceRegistration(BaseModel):
    """Model for registering a VyOS device."""

    name: str = Field(..., description="Unique identifier for the device")
    hostname: str = Field(..., description="IP address or hostname of VyOS device")
    apikey: str = Field(..., description="API key for authentication")
    version: Literal["1.4", "1.5"] = Field(..., description="VyOS version")
    protocol: Literal["http", "https"] = Field(
        default="https", description="Protocol to use"
    )
    port: int = Field(default=443, ge=1, le=65535, description="Port number")
    verify_ssl: bool = Field(
        default=False, description="Whether to verify SSL certificates"
    )
    timeout: int = Field(default=10, ge=1, description="Request timeout in seconds")


# ============================================================================
# Application Setup
# ============================================================================

# Device registry
device_registry = VyOSDeviceRegistry()

# Set device registry for routers
ethernet.set_device_registry(device_registry)
dummy.set_device_registry(device_registry)

# Include routers
app.include_router(ethernet.router)
app.include_router(dummy.router)


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/", tags=["root"])
async def read_root() -> dict:
    """API root endpoint with basic information."""
    return {
        "message": "VyOS Management API",
        "docs": "/docs",
        "supported_versions": ["1.4", "1.5"],
        "features": ["ethernet-interface", "dummy-interface"],
    }


# ============================================================================
# Device Management Endpoints
# ============================================================================


@app.post("/devices/register", tags=["device-management"], status_code=201)
async def register_device(device: DeviceRegistration) -> dict:
    """
    Register a VyOS device with its configuration and version.

    This allows the API to use version-aware commands when communicating
    with the device.
    """
    try:
        config = VyOSDeviceConfig(
            hostname=device.hostname,
            apikey=device.apikey,
            version=device.version,
            protocol=device.protocol,
            port=device.port,
            verify=device.verify_ssl,
            timeout=device.timeout,
        )
        device_registry.register(device.name, config)
        return {
            "success": True,
            "message": f"Device '{device.name}' registered successfully",
            "version": device.version,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/devices", tags=["device-management"])
async def list_devices() -> dict:
    """List all registered VyOS devices."""
    devices = device_registry.list_devices()
    device_info = []
    for name in devices:
        service = device_registry.get(name)
        device_info.append({"name": name, "version": service.get_version()})
    return {"devices": device_info}


@app.delete("/devices/{device_name}", tags=["device-management"])
async def unregister_device(device_name: str) -> dict:
    """Unregister a VyOS device."""
    device_registry.unregister(device_name)
    return {"success": True, "message": f"Device '{device_name}' unregistered"}


# ============================================================================
# Configuration Management Endpoints
# ============================================================================


@app.post("/vyos/{device_name}/config/refresh", tags=["config-management"])
async def refresh_device_config(device_name: str) -> dict:
    """
    Force refresh the full configuration from VyOS device and cache it.

    This endpoint will:
    1. Make an API call to VyOS to retrieve the full configuration
    2. Store it in the cache for faster subsequent reads
    3. Return summary information about the config

    Use this endpoint when you want to ensure you have the latest configuration.
    """
    try:
        service = device_registry.get(device_name)
        config = service.refresh_config()

        # Return summary info
        return {
            "success": True,
            "message": f"Configuration refreshed for device '{device_name}'",
            "cached": True,
            "config_keys": list(config.keys()) if config else [],
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vyos/{device_name}/config", tags=["config-management"])
async def get_device_config(device_name: str, refresh: bool = False) -> dict:
    """
    Get the full VyOS configuration (cached or fresh).

    Args:
        device_name: Name of the registered device
        refresh: If True, force refresh from VyOS. If False, use cache if available.

    Returns:
        Full VyOS configuration as JSON
    """
    try:
        service = device_registry.get(device_name)
        config = service.get_full_config(refresh=refresh)

        return {
            "success": True,
            "device": device_name,
            "cached": not refresh,
            "config": config,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Note: Feature-specific endpoints (Ethernet, Dummy, etc.) are in routers/
# ============================================================================
