import urllib3
urllib3.disable_warnings()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal

from vyos_service import VyOSDeviceConfig, VyOSDeviceRegistry

# Import routers
from routers import interface

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
# Pydantic Models - Batch Operations
# ============================================================================


class BatchOperation(BaseModel):
    """Model for a single batch operation."""

    op: Literal["set", "delete"] = Field(..., description="Operation type")
    path: List[str] = Field(..., description="Command path as list of strings")


class BatchRequest(BaseModel):
    """Model for batch operations request."""

    operations: List[BatchOperation] = Field(
        ..., description="List of operations to execute"
    )


class VyOSResponse(BaseModel):
    """Standard response from VyOS operations."""

    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None


# ============================================================================
# Application Setup
# ============================================================================

# Device registry
device_registry = VyOSDeviceRegistry()

# Set device registry for routers
interface.set_device_registry(device_registry)

# Include routers
app.include_router(interface.router)


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
        "features": ["interface"],
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
# Generic Batch Operations
# ============================================================================
# Note: Feature-specific endpoints (Interface, etc.) are in routers/
#       This endpoint is for advanced users who want to send raw command paths


@app.post("/vyos/{device_name}/batch", tags=["vyos-batch"])
async def execute_batch_operations(
    device_name: str, batch_request: BatchRequest
) -> VyOSResponse:
    """
    Execute multiple VyOS configuration operations in a single batch.

    This endpoint allows you to send multiple set/delete operations that
    will be executed together using configure_multiple_op for efficiency.

    Note: You must provide the correct command paths for the device's VyOS version.
    For version-aware operations, use the specific endpoints like /interface/batch.

    Example request body:
    ```json
    {
        "operations": [
            {
                "op": "set",
                "path": ["interfaces", "ethernet", "eth0", "address", "10.0.0.1/24"]
            },
            {
                "op": "set",
                "path": ["interfaces", "ethernet", "eth0", "description", "LAN"]
            },
            {
                "op": "delete",
                "path": ["interfaces", "ethernet", "eth1"]
            }
        ]
    }
    ```
    """
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()

        for operation in batch_request.operations:
            if operation.op == "set":
                batch.add_set(operation.path)
            elif operation.op == "delete":
                batch.add_delete(operation.path)

        response = service.execute_batch(batch)

        return VyOSResponse(
            success=response.status == 200,
            data=response.result,
            error=response.error if response.error else None
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
