# VyOS Version-Aware API

A FastAPI backend that translates simple JSON requests into correct VyOS commands based on the device version.

## What This Does

Your frontend sends simple requests like "configure interface" → This API translates it to the correct VyOS command based on version (1.4 vs 1.5) → Sends to VyOS in one efficient batch.

**Key Benefits:**
- ✅ Frontend doesn't need to know VyOS command syntax
- ✅ Handles version differences automatically (VyOS 1.4 vs 1.5)
- ✅ Batches multiple changes into ONE API call (faster!)
- ✅ Caches configuration for fast reads
- ✅ Clean, self-contained code - each interface type in its own complete file

---

## Quick Start

### 1. Install and Run

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

### 2. Register a VyOS Device

```bash
curl -X POST "http://127.0.0.1:8000/devices/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "router1",
    "hostname": "192.168.1.1",
    "apikey": "YOUR_API_KEY",
    "version": "1.4"
  }'
```

### 3. Pull Configuration (Cache It)

```bash
curl -X POST "http://127.0.0.1:8000/vyos/router1/config/refresh"
```

### 4. Configure Interfaces (Batch)

```bash
curl -X POST "http://127.0.0.1:8000/vyos/router1/ethernet/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "eth0",
    "operations": [
      {"op": "set_description", "value": "WAN Interface"},
      {"op": "set_address", "value": "10.0.0.1/24"},
      {"op": "set_mtu", "value": "1500"}
    ]
  }'
```

### 5. Read Interface Configuration

```bash
curl "http://127.0.0.1:8000/vyos/router1/ethernet/config"
```

### 6. View Interactive Docs

Visit `http://127.0.0.1:8000/docs` to see all endpoints and try them in your browser!

---

## How It Works (Simple Explanation)

```
┌─────────────┐
│  Frontend   │  Sends: {"interface": "eth0", "operations": [...]}
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Router (routers/interfaces/ethernet.py)        │
│  - Receives request                                     │
│  - Validates JSON with Pydantic models                  │
│  - Calls builder                                        │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Builder (vyos_builders/interfaces/ethernet.py)         │
│  - Self-contained batch builder                         │
│  - Takes operations and builds batch                    │
│  - Calls mapper to get correct VyOS commands            │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Mapper (vyos_mappers/interfaces/ethernet.py)           │
│  - Self-contained command mapper                        │
│  - Knows VyOS version (1.4 or 1.5)                      │
│  - Returns correct command path                         │
│  - Example: ["interfaces", "ethernet", "eth0", ...]     │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  VyOS Device                                            │
│  Executes: set interfaces ethernet eth0 description WAN │
└─────────────────────────────────────────────────────────┘
```

**For READ operations:**
```
┌─────────────┐
│  Frontend   │  GET request
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Router (routers/interfaces/ethernet.py)        │
│  - Retrieves cached config from service                 │
│  - Calls mapper to parse VyOS data                      │
│  - Returns structured JSON                              │
└─────────────────────────────────────────────────────────┘
```

**In short:**
1. **Router** = API endpoint (receives/returns JSON) - self-contained per interface type
2. **Builder** = Builds batch of commands - self-contained per interface type
3. **Mapper** = Translates to/from VyOS syntax based on version - self-contained per interface type

---

## Project Structure Example

```
test/
├── app.py                              # Main FastAPI app (device management)
├── vyos_service.py                     # VyOS connection & config caching
│
├── routers/                            # API endpoints
│   └── interfaces/                     # Interface endpoints by type
│       ├── ethernet.py                 # COMPLETE ethernet endpoints (GET /config, POST /batch)
│       ├── dummy.py                    # COMPLETE dummy endpoints (GET /config, POST /batch)
│       └── __init__.py
│
├── vyos_builders/                      # Batch builders
│   ├── __init__.py                     # Exports: EthernetBatchBuilder, DummyBatchBuilder
│   └── interfaces/                     # Interface builders by type
│       ├── ethernet.py                 # COMPLETE ethernet batch builder
│       ├── dummy.py                    # COMPLETE dummy batch builder
│       └── __init__.py
│
└── vyos_mappers/                       # VyOS command translation & parsing
    ├── __init__.py                     # CommandMapperRegistry
    ├── base.py                         # BaseFeatureMapper (version storage)
    └── interfaces/                     # Interface mappers by type
        ├── ethernet.py                 # COMPLETE ethernet mapper (commands + parsing)
        ├── dummy.py                    # COMPLETE dummy mapper (commands + parsing)
        └── __init__.py
```

### Key Architecture Principles Examples

**✅ Self-Contained Files:**
- Each interface type (ethernet, dummy) has its own COMPLETE file in each layer
- All models, operations, and logic for that type are in ONE file
- No shared base files in the interfaces directories

**✅ Separation by Interface Type:**
- Even though ethernet and dummy share common operations (description, address, MTU, etc.), they are in SEPARATE files
- This makes it easy to see what each interface type supports
- Easy to add interface-specific features (e.g., duplex/speed for ethernet only)

**✅ No Inheritance Complexity:**
- Builders and mappers inherit only from the base feature classes
- No mixin patterns or shared interface base classes
- Everything for one interface type is explicit and visible

---

## How to Add a New Interface Type

Let's say you want to add **Bridge** interface support. Here's the process:

### Important Rule: Keep It Separate!

**Even if bridges share common operations with ethernet (like description, address, MTU), create SEPARATE self-contained files.** This makes the code easier to understand and maintain.

---

### Step 1: Create the Mapper

**File:** `vyos_mappers/interfaces/bridge.py`

This defines ALL bridge commands and parsing logic in ONE file:

```python
"""
Bridge Interface Command Mapper

Handles bridge-specific interface commands.
Provides both command path generation (for writes) and config parsing (for reads).
"""

from typing import List, Dict, Any
from ..base import BaseFeatureMapper


class BridgeInterfaceMapper(BaseFeatureMapper):
    """Bridge interface mapper with all bridge interface operations"""

    def __init__(self, version: str):
        """Initialize with VyOS version."""
        super().__init__(version)
        self.interface_type = "bridge"

    # ========================================================================
    # Command Path Methods (for WRITE operations)
    # ========================================================================

    def get_description(self, interface: str, description: str) -> List[str]:
        """Get command path for setting interface description."""
        return ["interfaces", self.interface_type, interface, "description", description]

    def get_description_path(self, interface: str) -> List[str]:
        """Get command path for description property (for deletion)."""
        return ["interfaces", self.interface_type, interface, "description"]

    def get_address(self, interface: str, address: str) -> List[str]:
        """Get command path for setting interface address."""
        return ["interfaces", self.interface_type, interface, "address", address]

    def get_member(self, interface: str, member: str) -> List[str]:
        """Get command path for adding bridge member (bridge-specific)."""
        return ["interfaces", self.interface_type, interface, "member", "interface", member]

    # Add all other bridge operations...

    # ========================================================================
    # Config Parsing Methods (for READ operations)
    # ========================================================================

    def parse_single_interface(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single bridge interface configuration from VyOS."""
        if self.version == "1.4":
            return self._parse_interface_v14(name, config)
        elif self.version == "1.5":
            return self._parse_interface_v15(name, config)
        else:
            return self._parse_interface_v15(name, config)

    def _parse_interface_v14(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse bridge interface configuration for VyOS 1.4.x."""
        addresses = []
        if "address" in config:
            addr = config["address"]
            if isinstance(addr, list):
                addresses = addr
            elif isinstance(addr, str):
                addresses = [addr]

        # Parse bridge members
        members = []
        if "member" in config and "interface" in config["member"]:
            member_config = config["member"]["interface"]
            if isinstance(member_config, dict):
                members = list(member_config.keys())

        return {
            "name": name,
            "type": self.interface_type,
            "addresses": addresses,
            "description": config.get("description"),
            "members": members,
            "disable": "disable" in config if "disable" in config else None,
        }

    def _parse_interface_v15(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse bridge interface configuration for VyOS 1.5.x."""
        # Same as 1.4 for now, but can differ in future
        return self._parse_interface_v14(name, config)

    def parse_interfaces_of_type(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse all bridge interfaces."""
        interfaces = []
        for iface_name, iface_config in config.items():
            if not isinstance(iface_config, dict):
                continue
            interface = self.parse_single_interface(iface_name, iface_config)
            interfaces.append(interface)

        return {
            "interfaces": interfaces,
            "total": len(interfaces),
            "by_type": {self.interface_type: len(interfaces)},
            "by_vrf": {},
        }
```

---

### Step 2: Create the Builder

**File:** `vyos_builders/interfaces/bridge.py`

This provides ALL batch operations for bridges in ONE file:

```python
"""
Bridge Interface Batch Builder

Provides all bridge interface batch operations.
"""

from typing import List, Dict, Any
from vyos_mappers import CommandMapperRegistry


class BridgeInterfaceBuilderMixin:
    """Complete batch builder for bridge interface operations"""

    def __init__(self, version: str):
        """Initialize bridge interface batch builder."""
        self.version = version
        self._operations: List[Dict[str, Any]] = []
        self.mappers = CommandMapperRegistry.get_all_mappers(version)
        self.interface_mapper_key = "interface_bridge"

    # ========================================================================
    # Core Batch Operations
    # ========================================================================

    def add_set(self, path: List[str]) -> "BridgeInterfaceBuilderMixin":
        """Add a 'set' operation to the batch."""
        self._operations.append({"op": "set", "path": path})
        return self

    def add_delete(self, path: List[str]) -> "BridgeInterfaceBuilderMixin":
        """Add a 'delete' operation to the batch."""
        self._operations.append({"op": "delete", "path": path})
        return self

    def get_operations(self) -> List[Dict[str, Any]]:
        """Get the list of operations."""
        return self._operations.copy()

    def is_empty(self) -> bool:
        """Check if the batch is empty."""
        return len(self._operations) == 0

    # ========================================================================
    # Bridge Interface Operations
    # ========================================================================

    def set_interface_description(
        self, interface: str, description: str
    ) -> "BridgeInterfaceBuilderMixin":
        """Set interface description"""
        path = self.mappers[self.interface_mapper_key].get_description(interface, description)
        return self.add_set(path)

    def add_bridge_member(
        self, interface: str, member: str
    ) -> "BridgeInterfaceBuilderMixin":
        """Add interface to bridge (bridge-specific)"""
        path = self.mappers[self.interface_mapper_key].get_member(interface, member)
        return self.add_set(path)

    # Add all other bridge operations...
```

---

### Step 3: Create the Router

**File:** `routers/interfaces/bridge.py`

This creates ALL endpoints for bridges in ONE file:

```python
"""
Bridge Interface Configuration Endpoints

All bridge interface endpoints for VyOS configuration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from vyos_service import VyOSDeviceRegistry

router = APIRouter(prefix="/vyos/{device_name}/bridge", tags=["bridge-interface"])

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
    interface: str = Field(..., description="Interface name (e.g., br0)")
    description: str = Field(..., description="Interface description")


class BridgeMember(BaseModel):
    """Model for bridge member operations."""
    interface: str = Field(..., description="Bridge name (e.g., br0)")
    member: str = Field(..., description="Member interface (e.g., eth0)")


class InterfaceBatchRequest(BaseModel):
    """Model for batch interface configuration."""
    interface: str = Field(..., description="Interface name (e.g., br0)")
    operations: List[Dict[str, str]] = Field(
        ...,
        description="List of interface operations"
    )


class VyOSResponse(BaseModel):
    """Standard response from VyOS operations."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None


# ============================================================================
# Response Models (for READ operations)
# ============================================================================

class BridgeInterfaceConfigResponse(BaseModel):
    """Bridge interface configuration from VyOS (read operation)"""
    name: str = Field(..., description="Interface name (e.g., br0)")
    type: str = Field(..., description="Interface type (bridge)")
    addresses: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    members: List[str] = Field(default_factory=list, description="Bridge member interfaces")
    disable: Optional[bool] = None


class BridgeInterfacesConfigResponse(BaseModel):
    """Response containing all bridge interface configurations"""
    interfaces: List[BridgeInterfaceConfigResponse] = Field(default_factory=list)
    total: int = Field(0)
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_vrf: Dict[str, int] = Field(default_factory=dict)


# ============================================================================
# READ Operations (GET)
# ============================================================================

@router.get("/config", response_model=BridgeInterfacesConfigResponse)
async def get_bridge_config(device_name: str) -> BridgeInterfacesConfigResponse:
    """Get all bridge interface configurations from VyOS."""
    from vyos_mappers.interfaces import BridgeInterfaceMapper

    try:
        service = device_registry.get(device_name)
        full_config = service.get_full_config()
        raw_config = full_config.get("interfaces", {}).get("bridge", {})

        mapper = BridgeInterfaceMapper(service.get_version())
        parsed_data = mapper.parse_interfaces_of_type(raw_config)

        return BridgeInterfacesConfigResponse(**parsed_data)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Bridge Interface Batch Endpoint
# ============================================================================

@router.post("/batch")
async def configure_interface_batch(
    device_name: str, request: InterfaceBatchRequest
) -> VyOSResponse:
    """
    Configure bridge interface using batch operations.

    Supported operations:
    - set_description
    - delete_description
    - set_address
    - delete_address
    - add_member
    - delete_member
    - delete_interface
    """
    try:
        service = device_registry.get(device_name)
        batch = service.create_bridge_batch()

        for operation in request.operations:
            op_type = operation.get("op")
            value = operation.get("value")

            if not op_type:
                raise HTTPException(status_code=400, detail="Operation must have 'op' key")

            # Handle each operation type...
            if op_type == "set_description":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.set_interface_description(request.interface, value)
            elif op_type == "add_member":
                if not value:
                    raise HTTPException(status_code=400, detail=f"{op_type} requires a value")
                batch.add_bridge_member(request.interface, value)
            # ... handle all other operations

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
```

---

### Step 4: Register the Mapper

**File:** `vyos_mappers/__init__.py`

```python
from .interfaces.bridge import BridgeInterfaceMapper

CommandMapperRegistry.register_feature("interface_bridge", BridgeInterfaceMapper)
```

---

### Step 5: Register the Builder

**File:** `vyos_builders/__init__.py`

```python
from .interfaces import BridgeInterfaceBuilderMixin

BridgeBatchBuilder = BridgeInterfaceBuilderMixin

__all__ = [
    "EthernetBatchBuilder",
    "DummyBatchBuilder",
    "BridgeBatchBuilder",  # ← Add this
]
```

---

### Step 6: Add Service Method

**File:** `vyos_service.py`

```python
def create_bridge_batch(self) -> BridgeBatchBuilder:
    """Create a batch builder for bridge interfaces."""
    return BridgeBatchBuilder(self.config.version)
```

---

### Step 7: Register the Router

**File:** `app.py`

```python
from routers.interfaces import ethernet, dummy, bridge

bridge.set_device_registry(device_registry)
app.include_router(bridge.router)
```

---

## Quick Reference Checklist

When adding a new interface type (e.g., bridge, pppoe, vxlan), create these **self-contained** files:

```
☐ vyos_mappers/interfaces/INTERFACE_TYPE.py
   - Inherits from BaseFeatureMapper
   - Contains ALL command path methods (get_X, get_X_path)
   - Contains ALL parsing methods (_parse_interface_v14, _parse_interface_v15)
   - Typically 150-200 lines

☐ vyos_builders/interfaces/INTERFACE_TYPE.py
   - Self-contained builder class
   - Contains core batch operations (add_set, add_delete, etc.)
   - Contains ALL interface operation methods
   - Typically 120-150 lines

☐ routers/interfaces/INTERFACE_TYPE.py
   - Self-contained router with all endpoints
   - Contains ALL Pydantic models (request + response)
   - Contains GET /config endpoint
   - Contains POST /batch endpoint
   - Typically 300-350 lines

Then register in:
☐ vyos_mappers/__init__.py          - Add import and register_feature()
☐ vyos_builders/__init__.py         - Export the builder
☐ vyos_service.py                   - Add create_X_batch() method
☐ app.py                             - Import router and include it
```

---

## Architecture Patterns

### Configuration Caching (for READ operations)

```python
# In vyos_service.py
def get_full_config(self, refresh: bool = False) -> Dict[str, Any]:
    """Get full VyOS config (cached unless refresh=True)"""
    if self._cached_config is not None and not refresh:
        return self._cached_config

    response = self.device.show(path=["configuration", "json", "pretty"])
    self._cached_config = json.loads(response.result)
    return self._cached_config
```

### Version-Aware Parsing

```python
# In each mapper file
def parse_single_interface(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Version-aware parsing dispatcher"""
    if self.version == "1.4":
        return self._parse_interface_v14(name, config)
    elif self.version == "1.5":
        return self._parse_interface_v15(name, config)
    else:
        return self._parse_interface_v15(name, config)
```

### Batch Operations

```python
# Single operation
{
    "interface": "eth0",
    "operations": [
        {"op": "set_description", "value": "WAN"}
    ]
}

# Multiple operations in one batch
{
    "interface": "eth0",
    "operations": [
        {"op": "set_description", "value": "WAN"},
        {"op": "set_address", "value": "10.0.0.1/24"},
        {"op": "set_mtu", "value": "9000"},
        {"op": "enable"}
    ]
}
```

---

## API Endpoints Example

Visit `http://127.0.0.1:8000/docs` for full interactive documentation.

### Device Management
- `POST /devices/register` - Register a VyOS device
- `GET /devices` - List all devices
- `DELETE /devices/{name}` - Unregister a device

### Configuration Management
- `POST /vyos/{device}/config/refresh` - Pull and cache full config
- `GET /vyos/{device}/config` - Get cached config

### Ethernet Interfaces
- `GET /vyos/{device}/ethernet/config` - Read all ethernet interfaces
- `POST /vyos/{device}/ethernet/batch` - Configure ethernet interface (batch)

### Dummy Interfaces
- `GET /vyos/{device}/dummy/config` - Read all dummy interfaces
- `POST /vyos/{device}/dummy/batch` - Configure dummy interface (batch)

---

## Tips

**Version Differences:**
- Handle version differences in the **mapper** (`_parse_interface_v14` vs `_parse_interface_v15`)
- The **builder** and **router** don't need to know about versions!

**Testing:**
- Use the interactive docs at `/docs` to test endpoints
- Each endpoint validates input automatically (Pydantic)
- All errors return helpful messages

**Best Practices:**
- Always refresh config before reading: `POST /vyos/{device}/config/refresh`
- Use batch operations for multiple changes
- Keep interface types in separate self-contained files
- Don't try to share code between interface types - clarity > DRY

---

## Support

For questions or issues with VyOS commands, refer to:
- VyOS 1.4 Documentation: https://docs.vyos.io/en/sagitta/
- VyOS 1.5 Documentation: https://docs.vyos.io/en/latest/

For API issues, check the interactive docs at `/docs`
