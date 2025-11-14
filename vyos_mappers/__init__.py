"""
VyOS Command Mappers - Modular structure

Each feature category (interfaces, firewall, nat, etc.) has its own subdirectory.
This keeps the codebase organized and maintainable as it grows.
"""

from .base import BaseFeatureMapper, CommandMapperRegistry
from .interfaces import EthernetInterfaceMapper, DummyInterfaceMapper
from .interfaces.ethernet_versions import get_ethernet_mapper

# Auto-register all mappers
# Ethernet uses factory for version-specific mappers
CommandMapperRegistry.register_feature("interface_ethernet", get_ethernet_mapper)
# Dummy uses direct class (no version differences)
CommandMapperRegistry.register_feature("interface_dummy", DummyInterfaceMapper)

__all__ = [
    "BaseFeatureMapper",
    "CommandMapperRegistry",
    "EthernetInterfaceMapper",
    "DummyInterfaceMapper",
]
