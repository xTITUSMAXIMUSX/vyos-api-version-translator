"""
VyOS Command Mappers - Modular structure

Each feature category (interfaces, firewall, nat, etc.) has its own subdirectory.
This keeps the codebase organized and maintainable as it grows.
"""

from .base import BaseFeatureMapper, CommandMapperRegistry
from .interfaces import EthernetInterfaceMapper, DummyInterfaceMapper

# Auto-register all mappers
CommandMapperRegistry.register_feature("interface_ethernet", EthernetInterfaceMapper)
CommandMapperRegistry.register_feature("interface_dummy", DummyInterfaceMapper)

__all__ = [
    "BaseFeatureMapper",
    "CommandMapperRegistry",
    "EthernetInterfaceMapper",
    "DummyInterfaceMapper",
]
