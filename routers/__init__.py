"""
FastAPI Routers

Each router handles a specific VyOS feature:
- interface: Interface configuration endpoints
"""

from .interface import router as interface_router

__all__ = ["interface_router"]
