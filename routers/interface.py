"""
Interface Configuration Endpoints

All interface-related endpoints for VyOS configuration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal

from vyos_service import VyOSDeviceRegistry

# Router for interface endpoints
router = APIRouter(prefix="/vyos/{device_name}/interface", tags=["configure-interface"])

# Shared device registry (will be set from app.py)
device_registry: VyOSDeviceRegistry = None


def set_device_registry(registry: VyOSDeviceRegistry):
    """Set the device registry for this router."""
    global device_registry
    device_registry = registry


# ============================================================================
# Pydantic Models
# ============================================================================


class InterfaceDescription(BaseModel):
    """Model for setting interface description."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")
    description: str = Field(..., description="Interface description")


class InterfaceDelete(BaseModel):
    """Model for deleting an interface."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")


class InterfaceAddress(BaseModel):
    """Model for interface address operations."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")
    address: str = Field(..., description="IP address in CIDR notation (e.g., 10.0.0.1/24)")


class InterfaceMTU(BaseModel):
    """Model for setting interface MTU."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")
    mtu: str = Field(..., description="MTU value (e.g., 1500)")


class InterfaceDuplex(BaseModel):
    """Model for setting interface duplex."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")
    duplex: str = Field(..., description="Duplex setting (auto, half, full)")


class InterfaceSpeed(BaseModel):
    """Model for setting interface speed."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")
    speed: str = Field(..., description="Speed setting (auto, 10, 100, 1000, etc.)")


class InterfaceBatchRequest(BaseModel):
    """Model for batch interface configuration."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")
    operations: List[Dict[str, str]] = Field(
        ...,
        description="List of interface operations",
        example=[
            {"op": "set_description", "value": "WAN Interface"},
            {"op": "set_address", "value": "10.0.0.1/24"},
            {"op": "set_mtu", "value": "1500"}
        ]
    )


class VyOSResponse(BaseModel):
    """Standard response from VyOS operations."""

    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None


# ============================================================================
# Interface Endpoints
# ============================================================================


@router.post("/description/set")
async def set_interface_description(
    device_name: str, config: InterfaceDescription
) -> VyOSResponse:
    """Set interface description."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.set_interface_description(config.interface, config.description)
        response = service.execute_batch(batch)

        return VyOSResponse(
            success=response.status == 200,
            data=response.result,
            error=response.error if response.error else None
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/address/set")
async def set_interface_address(
    device_name: str, config: InterfaceAddress
) -> VyOSResponse:
    """Set interface IP address."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.set_interface_address(config.interface, config.address)
        response = service.execute_batch(batch)

        return VyOSResponse(
            success=response.status == 200,
            data=response.result,
            error=response.error if response.error else None
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/address/delete")
async def delete_interface_address(
    device_name: str, config: InterfaceAddress
) -> VyOSResponse:
    """Delete interface IP address."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.delete_interface_address(config.interface, config.address)
        response = service.execute_batch(batch)

        return VyOSResponse(
            success=response.status == 200,
            data=response.result,
            error=response.error if response.error else None
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mtu/set")
async def set_interface_mtu(
    device_name: str, config: InterfaceMTU
) -> VyOSResponse:
    """Set interface MTU."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.set_interface_mtu(config.interface, config.mtu)
        response = service.execute_batch(batch)

        return VyOSResponse(
            success=response.status == 200,
            data=response.result,
            error=response.error if response.error else None
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/duplex/set")
async def set_interface_duplex(
    device_name: str, config: InterfaceDuplex
) -> VyOSResponse:
    """Set interface duplex mode."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.set_interface_duplex(config.interface, config.duplex)
        response = service.execute_batch(batch)

        return VyOSResponse(
            success=response.status == 200,
            data=response.result,
            error=response.error if response.error else None
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speed/set")
async def set_interface_speed(
    device_name: str, config: InterfaceSpeed
) -> VyOSResponse:
    """Set interface speed."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.set_interface_speed(config.interface, config.speed)
        response = service.execute_batch(batch)

        return VyOSResponse(
            success=response.status == 200,
            data=response.result,
            error=response.error if response.error else None
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_interface(
    device_name: str, config: InterfaceDelete
) -> VyOSResponse:
    """Delete entire interface configuration."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.delete_interface(config.interface)
        response = service.execute_batch(batch)

        return VyOSResponse(
            success=response.status == 200,
            data=response.result,
            error=response.error if response.error else None
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def configure_interface_batch(
    device_name: str, request: InterfaceBatchRequest
) -> VyOSResponse:
    """
    Configure interface using batch operations.

    This endpoint allows you to configure multiple interface settings
    in a single API call. All operations are version-aware and will be
    sent to VyOS in one batch.

    Example request body:
    ```json
    {
        "interface": "eth0",
        "operations": [
            {"op": "set_description", "value": "WAN Interface"},
            {"op": "set_address", "value": "10.0.0.1/24"},
            {"op": "set_mtu", "value": "1500"},
            {"op": "set_duplex", "value": "auto"},
            {"op": "set_speed", "value": "auto"},
            {"op": "delete_address", "value": "192.168.1.1/24"},
            {"op": "delete_interface"}
        ]
    }
    ```

    Supported operations:
    - set_description (requires value)
    - set_address (requires value)
    - delete_address (requires value)
    - set_mtu (requires value)
    - set_duplex (requires value)
    - set_speed (requires value)
    - delete_interface (no value needed - deletes entire interface)
    """
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()

        # Process each operation
        for operation in request.operations:
            op_type = operation.get("op")
            value = operation.get("value")

            if not op_type:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid operation: {operation}. Must have 'op' key"
                )

            # Map operation to batch method
            if op_type == "set_description":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_description(request.interface, value)
            elif op_type == "set_address":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_address(request.interface, value)
            elif op_type == "delete_address":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.delete_interface_address(request.interface, value)
            elif op_type == "set_mtu":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_mtu(request.interface, value)
            elif op_type == "set_duplex":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_duplex(request.interface, value)
            elif op_type == "set_speed":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_speed(request.interface, value)
            elif op_type == "delete_interface":
                # Delete entire interface - no value needed
                batch.delete_interface(request.interface)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported operation: {op_type}"
                )

        # Execute the batch
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
