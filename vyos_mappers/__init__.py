"""
VyOS Command Mappers - Modular structure

Each feature (DHCP, interfaces, firewall, etc.) has its own mapper file.
This keeps the codebase organized and maintainable.
"""

from .base import BaseFeatureMapper, CommandMapperRegistry
from .interface import InterfaceMapper

# Auto-register all mappers
CommandMapperRegistry.register_feature("interface", InterfaceMapper)

__all__ = [
    "BaseFeatureMapper",
    "CommandMapperRegistry",
    "InterfaceMapper",
]
