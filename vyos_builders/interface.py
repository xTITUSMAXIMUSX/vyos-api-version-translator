"""
Interface Batch Builder Mixin

Provides interface-specific batch operations.
"""


class InterfaceBuilderMixin:
    """Mixin for interface batch operations"""

    def set_interface_description(
        self, interface: str, description: str
    ) -> "InterfaceBuilderMixin":
        """Set interface description"""
        path = self.mappers["interface"].get_description(interface, description)
        return self.add_set(path)

    def set_interface_address(
        self, interface: str, address: str
    ) -> "InterfaceBuilderMixin":
        """Set interface address"""
        path = self.mappers["interface"].get_address(interface, address)
        return self.add_set(path)

    def delete_interface_address(
        self, interface: str, address: str
    ) -> "InterfaceBuilderMixin":
        """Delete interface address"""
        path = self.mappers["interface"].get_address(interface, address)
        return self.add_delete(path)

    def set_interface_mtu(
        self, interface: str, mtu: str
    ) -> "InterfaceBuilderMixin":
        """Set interface MTU"""
        path = self.mappers["interface"].get_mtu(interface, mtu)
        return self.add_set(path)

    def set_interface_duplex(
        self, interface: str, duplex: str
    ) -> "InterfaceBuilderMixin":
        """Set interface duplex"""
        path = self.mappers["interface"].get_duplex(interface, duplex)
        return self.add_set(path)

    def set_interface_speed(
        self, interface: str, speed: str
    ) -> "InterfaceBuilderMixin":
        """Set interface speed"""
        path = self.mappers["interface"].get_speed(interface, speed)
        return self.add_set(path)

    def delete_interface(self, interface: str) -> "InterfaceBuilderMixin":
        """Delete entire interface configuration"""
        path = self.mappers["interface"].get_interface(interface)
        return self.add_delete(path)
