"""
Interface Command Mapper

Handles version-specific interface command translation.
"""

from typing import List
from .base import BaseFeatureMapper


class InterfaceMapper(BaseFeatureMapper):
    """Interface command mapper supporting VyOS 1.4 and 1.5"""

    def get_description(self, interface: str, description: str) -> List[str]:
        """Get command path for setting interface description."""
        # Same syntax for both 1.4 and 1.5
        return ["interfaces", "ethernet", interface, "description", description]

    def get_address(self, interface: str, address: str) -> List[str]:
        """Get command path for setting interface address."""
        # Same syntax for both 1.4 and 1.5
        return ["interfaces", "ethernet", interface, "address", address]

    def get_mtu(self, interface: str, mtu: str) -> List[str]:
        """Get command path for setting interface MTU."""
        # Same syntax for both 1.4 and 1.5
        return ["interfaces", "ethernet", interface, "mtu", mtu]

    def get_duplex(self, interface: str, duplex: str) -> List[str]:
        """Get command path for setting interface duplex."""
        # Same syntax for both 1.4 and 1.5
        return ["interfaces", "ethernet", interface, "duplex", duplex]

    def get_speed(self, interface: str, speed: str) -> List[str]:
        """Get command path for setting interface speed."""
        # Same syntax for both 1.4 and 1.5
        return ["interfaces", "ethernet", interface, "speed", speed]

    def get_interface(self, interface: str) -> List[str]:
        """Get command path for an interface (for deletion)."""
        # Same syntax for both 1.4 and 1.5
        return ["interfaces", "ethernet", interface]
