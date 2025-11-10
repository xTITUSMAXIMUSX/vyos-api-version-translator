# VyOS Version-Aware API

A FastAPI backend that translates simple JSON requests into correct VyOS commands based on the device version.

## What This Does

Your frontend sends simple requests like "set interface description" → This API translates it to the correct VyOS command based on version (1.4 vs 1.5) → Sends to VyOS in one efficient batch.

**Key Benefits:**
- ✅ Frontend doesn't need to know VyOS command syntax
- ✅ Handles version differences automatically (VyOS 1.4 vs 1.5)
- ✅ Batches multiple changes into ONE API call (faster!)
- ✅ Clean, modular code - each feature in its own file

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

### 3. Configure an Interface

```bash
curl -X POST "http://127.0.0.1:8000/vyos/router1/interface/description/set" \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "eth0",
    "description": "WAN Interface"
  }'
```

### 4. View Interactive Docs

Visit `http://127.0.0.1:8000/docs` to see all endpoints and try them in your browser!

---

## How It Works (Simple Explanation)

```
┌─────────────┐
│  Frontend   │  Sends: {"interface": "eth0", "description": "WAN"}
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Router (routers/interface.py)                  │
│  - Receives request                                     │
│  - Validates JSON                                       │
│  - Calls builder                                        │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Builder (vyos_builders/interface.py)                   │
│  - Takes simple parameters                              │
│  - Calls mapper to get correct command                  │
│  - Adds to batch                                        │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Mapper (vyos_mappers/interface.py)                     │
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

**In short:**
1. **Router** = API endpoint (receives JSON)
2. **Builder** = Builds batch of commands
3. **Mapper** = Translates to correct VyOS syntax based on version

---

## Project Structure

```
test/
├── app.py                      # Main FastAPI app (device management)
├── vyos_service.py             # VyOS connection service
│
├── routers/                    # API endpoints (one file per feature)
│   ├── interface.py           # Interface endpoints
│   └── (add more features here)
│
├── vyos_builders/              # Build batches (one file per feature)
│   ├── base.py                # Base builder class
│   ├── interface.py           # Interface batch operations
│   └── (add more features here)
│
└── vyos_mappers/               # Version translation (one file per feature)
    ├── base.py                # Base mapper class
    ├── interface.py           # Interface command mapping
    └── (add more features here)
```

---

## How to Add a New Feature

Let's say you want to add **Static Routes** support. Here's the process:

### Step 1: Create the Mapper

**File:** `vyos_mappers/static_routes.py`

This defines the VyOS commands for different versions:

```python
from typing import List
from .base import BaseFeatureMapper

class StaticRoutesMapper(BaseFeatureMapper):
    """Maps static route commands for VyOS 1.4 and 1.5"""

    def get_route(self, destination: str, next_hop: str) -> List[str]:
        """Get command path for a static route."""
        # Same for both 1.4 and 1.5
        return ["protocols", "static", "route", destination, "next-hop", next_hop]
```

---

### Step 2: Create the Builder

**File:** `vyos_builders/static_routes.py`

This provides high-level methods to add routes to a batch:

```python
class StaticRoutesBuilderMixin:
    """Mixin for static route batch operations"""

    def set_static_route(self, destination: str, next_hop: str):
        """Add a static route"""
        path = self.mappers["static_routes"].get_route(destination, next_hop)
        return self.add_set(path)

    def delete_static_route(self, destination: str, next_hop: str):
        """Delete a static route"""
        path = self.mappers["static_routes"].get_route(destination, next_hop)
        return self.add_delete(path)
```

---

### Step 3: Register the Mapper

**File:** `vyos_mappers/__init__.py`

Add these two lines:

```python
from .static_routes import StaticRoutesMapper  # ← Add import

CommandMapperRegistry.register_feature("static_routes", StaticRoutesMapper)  # ← Add registration
```

---

### Step 4: Register the Builder

**File:** `vyos_builders/__init__.py`

Add to the imports and class:

```python
from .static_routes import StaticRoutesBuilderMixin  # ← Add import

class VersionAwareBatchBuilder(
    InterfaceBuilderMixin,
    StaticRoutesBuilderMixin,  # ← Add here
    BaseBatchBuilder
):
    """Complete batch builder with all features."""
    pass
```

---

### Step 5: Create the Router (API Endpoints)

**File:** `routers/static_routes.py`

This creates the FastAPI endpoints:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional

from vyos_service import VyOSDeviceRegistry

router = APIRouter(prefix="/vyos/{device_name}/routes", tags=["vyos-routes"])

device_registry: VyOSDeviceRegistry = None

def set_device_registry(registry: VyOSDeviceRegistry):
    global device_registry
    device_registry = registry

# Pydantic Models
class StaticRoute(BaseModel):
    destination: str = Field(..., description="Destination network (e.g., 10.0.0.0/24)")
    next_hop: str = Field(..., description="Next hop IP address")

class VyOSResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

# Endpoints
@router.post("/set")
async def set_static_route(
    device_name: str, config: StaticRoute
) -> VyOSResponse:
    """Add a static route."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.set_static_route(config.destination, config.next_hop)
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
async def delete_static_route(
    device_name: str, config: StaticRoute
) -> VyOSResponse:
    """Delete a static route."""
    try:
        service = device_registry.get(device_name)
        batch = service.create_version_aware_batch()
        batch.delete_static_route(config.destination, config.next_hop)
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

### Step 6: Register the Router

**File:** `app.py`

Add these lines:

```python
from routers import interface, static_routes  # ← Add import

# Set device registry for routers
interface.set_device_registry(device_registry)
static_routes.set_device_registry(device_registry)  # ← Add this

# Include routers
app.include_router(interface.router)
app.include_router(static_routes.router)  # ← Add this
```

---

### Done! Now You Can Use It:

```bash
curl -X POST "http://127.0.0.1:8000/vyos/router1/routes/set" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "10.0.0.0/24",
    "next_hop": "192.168.1.1"
  }'
```

---

## Quick Reference Checklist

When adding a new feature, create these files:

```
☐ vyos_mappers/FEATURE.py       - Command translation logic
☐ vyos_builders/FEATURE.py      - Batch operation methods
☐ routers/FEATURE.py            - API endpoints

Then register in:
☐ vyos_mappers/__init__.py      - Add import and register_feature()
☐ vyos_builders/__init__.py     - Add to VersionAwareBatchBuilder
☐ app.py                        - Import router and include it
```

---

## Current Features

### Interface Management
- Set/delete description
- Set/delete IP addresses
- Set MTU, duplex, speed
- Delete entire interface
- Batch operations

### Coming Soon
Add your own features following the guide above!

---

## Tips

**Version Differences:**
- Some VyOS commands are different between 1.4 and 1.5
- Handle this in the **mapper** using `if self.version == "1.4":`
- The **builder** and **router** don't need to know about versions!

**Testing:**
- Use the interactive docs at `/docs` to test endpoints
- Each endpoint validates input automatically (Pydantic)
- All errors return helpful messages

**Architecture:**
- Keep files small (~50-300 lines each)
- One feature = 3 files (mapper, builder, router)
- Each feature is independent

---

## API Endpoints

Visit `http://127.0.0.1:8000/docs` for full interactive documentation.

**Device Management:**
- `POST /devices/register` - Register a VyOS device
- `GET /devices` - List all devices
- `DELETE /devices/{name}` - Unregister a device

**Interface Management:**
- `POST /vyos/{device}/interface/description/set`
- `POST /vyos/{device}/interface/address/set`
- `POST /vyos/{device}/interface/address/delete`
- `POST /vyos/{device}/interface/mtu/set`
- `POST /vyos/{device}/interface/duplex/set`
- `POST /vyos/{device}/interface/speed/set`
- `POST /vyos/{device}/interface/delete`
- `POST /vyos/{device}/interface/batch`

**Generic Batch:**
- `POST /vyos/{device}/batch` - Send raw command paths

---

## Support

For questions or issues with VyOS commands, refer to:
- VyOS 1.4 Documentation: https://docs.vyos.io/en/sagitta/
- VyOS 1.5 Documentation: https://docs.vyos.io/en/latest/

For API issues, check the interactive docs at `/docs`
