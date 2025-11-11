"""
Ethernet Interface Configuration Endpoints

All ethernet-specific endpoints for VyOS configuration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from vyos_service import VyOSDeviceRegistry

# Router for ethernet interface endpoints
router = APIRouter(prefix="/vyos/{device_name}/ethernet", tags=["ethernet-interface"])

# Shared device registry (will be set from app.py)
device_registry: VyOSDeviceRegistry = None


def set_device_registry(registry: VyOSDeviceRegistry):
    """Set the device registry for this router."""
    global device_registry
    device_registry = registry


# ============================================================================
# Request Models (for WRITE operations)
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


class InterfaceVRF(BaseModel):
    """Model for VRF assignment."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")
    vrf: str = Field(..., description="VRF name")


class InterfaceDisable(BaseModel):
    """Model for disabling an interface."""

    interface: str = Field(..., description="Interface name (e.g., eth0)")


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
# Response Models (for READ operations)
# ============================================================================


class EthernetInterfaceConfigResponse(BaseModel):
    """Ethernet interface configuration from VyOS (read operation)"""

    name: str = Field(..., description="Interface name (e.g., eth0)")
    type: str = Field(..., description="Interface type (ethernet)")
    addresses: List[str] = Field(default_factory=list, description="IP addresses with CIDR notation")
    description: Optional[str] = Field(None, description="Interface description")
    vrf: Optional[str] = Field(None, description="VRF assignment")
    mtu: Optional[str] = Field(None, description="MTU value")

    # Ethernet-specific fields
    hw_id: Optional[str] = Field(None, description="Hardware MAC address")
    duplex: Optional[str] = Field(None, description="Duplex setting (auto/half/full)")
    speed: Optional[str] = Field(None, description="Speed setting (auto/10/100/1000/etc)")

    # Administrative state
    disable: Optional[bool] = Field(None, description="Whether interface is administratively disabled")

    class Config:
        populate_by_name = True


class EthernetInterfacesConfigResponse(BaseModel):
    """Response containing all ethernet interface configurations"""

    interfaces: List[EthernetInterfaceConfigResponse] = Field(
        default_factory=list,
        description="List of all ethernet interfaces"
    )
    total: int = Field(0, description="Total number of ethernet interfaces")

    # Statistics
    by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of interfaces by type (should be 'ethernet': N)"
    )
    by_vrf: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of interfaces by VRF"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "interfaces": [
                    {
                        "name": "eth0",
                        "type": "ethernet",
                        "addresses": ["192.168.1.1/24"],
                        "description": "WAN Interface",
                        "hw_id": "00:50:56:00:00:01",
                        "duplex": "auto",
                        "speed": "1000"
                    }
                ],
                "total": 1,
                "by_type": {"ethernet": 1},
                "by_vrf": {}
            }
        }


# ============================================================================
# READ Operations (GET)
# ============================================================================


@router.get("/config", response_model=EthernetInterfacesConfigResponse)
async def get_ethernet_config(device_name: str) -> EthernetInterfacesConfigResponse:
    """
    Get all ethernet interface configurations from VyOS.

    Returns configuration details including addresses, description, speed, duplex, hw_id, etc.
    """
    from vyos_mappers.interfaces import EthernetInterfaceMapper

    try:
        # Get service and retrieve raw config from cache
        service = device_registry.get(device_name)
        full_config = service.get_full_config()
        raw_config = full_config.get("interfaces", {}).get("ethernet", {})

        # Use mapper to parse config
        mapper = EthernetInterfaceMapper(service.get_version())
        parsed_data = mapper.parse_interfaces_of_type(raw_config)

        # Return as Pydantic model
        return EthernetInterfacesConfigResponse(**parsed_data)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Ethernet Interface Batch Endpoint
# ============================================================================


@router.post("/batch")
async def configure_interface_batch(
    device_name: str, request: InterfaceBatchRequest
) -> VyOSResponse:
    """
    Configure ethernet interface using batch operations.

    This is the main endpoint for configuring ethernet interfaces. All operations
    are version-aware and sent to VyOS in a single batch for efficiency.

    **Supported Operations:**

    | Operation | Value Required | Description |
    |-----------|----------------|-------------|
    | `set_description` | Yes | Set interface description |
    | `delete_description` | No | Remove interface description |
    | `set_address` | Yes | Add IP address (CIDR notation) |
    | `delete_address` | Yes | Remove IP address |
    | `set_mtu` | Yes | Set MTU value |
    | `delete_mtu` | No | Remove MTU (reset to default) |
    | `set_duplex` | Yes | Set duplex mode (auto/half/full) |
    | `delete_duplex` | No | Remove duplex (reset to default) |
    | `set_speed` | Yes | Set speed (auto/10/100/1000/etc) |
    | `delete_speed` | No | Remove speed (reset to default) |
    | `set_vrf` | Yes | Assign interface to VRF |
    | `delete_vrf` | Yes | Remove interface from VRF |
    | `disable` | No | Administratively disable interface |
    | `enable` | No | Enable interface (remove disable flag) |
    | `delete_interface` | No | Delete entire interface configuration |

    **Example Request:**
    ```json
    {
        "interface": "eth0",
        "operations": [
            {"op": "set_description", "value": "WAN Interface"},
            {"op": "set_address", "value": "10.0.0.1/24"},
            {"op": "set_address", "value": "2001:db8::1/64"},
            {"op": "delete_address", "value": "192.168.1.1/24"},
            {"op": "set_mtu", "value": "9000"},
            {"op": "set_duplex", "value": "full"},
            {"op": "set_speed", "value": "1000"},
            {"op": "set_vrf", "value": "MGMT"},
            {"op": "enable"}
        ]
    }
    ```

    **Example with Delete Operations:**
    ```json
    {
        "interface": "eth1",
        "operations": [
            {"op": "delete_description"},
            {"op": "delete_mtu"},
            {"op": "delete_duplex"},
            {"op": "delete_speed"}
        ]
    }
    ```
    """
    try:
        service = device_registry.get(device_name)
        batch = service.create_ethernet_batch()

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
            elif op_type == "delete_description":
                # Delete description - no value needed
                batch.delete_interface_description(request.interface)
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
            elif op_type == "delete_mtu":
                # Delete MTU - no value needed
                batch.delete_interface_mtu(request.interface)
            elif op_type == "set_duplex":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_duplex(request.interface, value)
            elif op_type == "delete_duplex":
                # Delete duplex - no value needed
                batch.delete_interface_duplex(request.interface)
            elif op_type == "set_speed":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_speed(request.interface, value)
            elif op_type == "delete_speed":
                # Delete speed - no value needed
                batch.delete_interface_speed(request.interface)
            elif op_type == "set_vrf":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_vrf(request.interface, value)
            elif op_type == "delete_vrf":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.delete_interface_vrf(request.interface, value)
            elif op_type == "disable":
                # Disable interface - no value needed
                batch.set_interface_disable(request.interface)
            elif op_type == "enable":
                # Enable interface - no value needed
                batch.delete_interface_disable(request.interface)
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
