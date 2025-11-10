"""
VyOS Service Layer - Modular Version

Uses the new modular mapper and builder structure.
Much cleaner and easier to maintain!
"""

from typing import Optional
from contextlib import contextmanager

from pyvyos import VyDevice
from pyvyos.core.rest_client import ApiResponse
from vyos_builders import VersionAwareBatchBuilder


class VyOSDeviceConfig:
    """Configuration for a VyOS device."""

    def __init__(
        self,
        hostname: str,
        apikey: str,
        version: str,
        protocol: str = "https",
        port: int = 443,
        verify: bool = False,
        timeout: int = 10,
    ):
        self.hostname = hostname
        self.apikey = apikey
        self.version = version
        self.protocol = protocol
        self.port = port
        self.verify = verify
        self.timeout = timeout


class VyOSService:
    """
    Service for managing VyOS devices with version-aware commands and batching.
    """

    def __init__(self, device_config: VyOSDeviceConfig):
        """Initialize VyOS service."""
        self.config = device_config
        self.device = VyDevice(
            hostname=device_config.hostname,
            apikey=device_config.apikey,
            protocol=device_config.protocol,
            port=device_config.port,
            verify=device_config.verify,
            timeout=device_config.timeout,
        )

    def get_version(self) -> str:
        """Get the VyOS version for this device."""
        return self.config.version

    def create_version_aware_batch(self) -> VersionAwareBatchBuilder:
        """
        Create a version-aware batch builder for this device.

        The builder automatically uses correct command syntax based on version.
        """
        return VersionAwareBatchBuilder(self.config.version)

    def execute_batch(self, batch: VersionAwareBatchBuilder) -> ApiResponse:
        """Execute a batch of operations using configure_multiple_op."""
        if batch.is_empty():
            raise ValueError("Cannot execute empty batch")

        operations = batch.get_operations()
        return self.device.configure_multiple_op(op_path=operations)

    @contextmanager
    def batch_context(self):
        """
        Context manager for building and executing batch operations.

        Example:
            >>> with service.batch_context() as batch:
            ...     batch.set_dhcp_default_router("LAN", "10.10.10.0/24", "10.10.10.1")
            ...     batch.set_interface_description("eth0", "WAN")
        """
        batch = VersionAwareBatchBuilder(self.config.version)
        yield batch
        if not batch.is_empty():
            self.execute_batch(batch)


class VyOSDeviceRegistry:
    """Registry for managing multiple VyOS devices."""

    def __init__(self):
        self._devices = {}

    def register(self, name: str, config: VyOSDeviceConfig) -> None:
        """Register a VyOS device."""
        self._devices[name] = VyOSService(config)

    def get(self, name: str) -> VyOSService:
        """Get a registered VyOS service by name."""
        if name not in self._devices:
            raise KeyError(f"Device '{name}' not found in registry")
        return self._devices[name]

    def unregister(self, name: str) -> None:
        """Unregister a device."""
        self._devices.pop(name, None)

    def list_devices(self) -> list:
        """Get list of registered device names."""
        return list(self._devices.keys())

    def clear(self) -> None:
        """Clear all registered devices."""
        self._devices.clear()
