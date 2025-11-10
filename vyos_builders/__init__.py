"""
VyOS Batch Builders - Modular structure

Each feature (DHCP, interfaces, firewall, etc.) has its own builder mixin.
These are combined to create a comprehensive batch builder.
"""

from .base import BaseBatchBuilder
from .interface import InterfaceBuilderMixin


class VersionAwareBatchBuilder(
    InterfaceBuilderMixin,
    BaseBatchBuilder
):
    """
    Complete batch builder with all features.

    To add new features, just add a new mixin class here.
    """
    pass


__all__ = [
    "BaseBatchBuilder",
    "InterfaceBuilderMixin",
    "VersionAwareBatchBuilder",
]
