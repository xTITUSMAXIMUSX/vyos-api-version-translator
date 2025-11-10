"""
Base Batch Builder

Provides core batching functionality that all builders use.
"""

from typing import List, Dict, Any
from vyos_mappers import CommandMapperRegistry


class BaseBatchBuilder:
    """
    Base batch builder with core operations.

    Feature-specific builders inherit from this and add their own methods.
    """

    def __init__(self, version: str):
        self.version = version
        self._operations: List[Dict[str, Any]] = []

        # Get all feature mappers for this version
        self.mappers = CommandMapperRegistry.get_all_mappers(version)

    def add_set(self, path: List[str]) -> "BaseBatchBuilder":
        """Add a 'set' operation to the batch."""
        self._operations.append({"op": "set", "path": path})
        return self

    def add_delete(self, path: List[str]) -> "BaseBatchBuilder":
        """Add a 'delete' operation to the batch."""
        self._operations.append({"op": "delete", "path": path})
        return self

    def add_multiple_sets(self, paths: List[List[str]]) -> "BaseBatchBuilder":
        """Add multiple 'set' operations to the batch."""
        for path in paths:
            self.add_set(path)
        return self

    def clear(self) -> None:
        """Clear all operations from the batch."""
        self._operations = []

    def get_operations(self) -> List[Dict[str, Any]]:
        """Get the list of operations."""
        return self._operations.copy()

    def operation_count(self) -> int:
        """Get the number of operations in the batch."""
        return len(self._operations)

    def is_empty(self) -> bool:
        """Check if the batch is empty."""
        return len(self._operations) == 0
