"""
Base classes for VyOS command mappers.

Provides the foundation for version-specific command translation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Type


class BaseFeatureMapper(ABC):
    """
    Base class for feature-specific mappers.

    Each feature (DHCP, interfaces, firewall, etc.) creates its own
    mapper class that inherits from this.
    """

    def __init__(self, version: str):
        self.version = version


class CommandMapperRegistry:
    """
    Registry for all feature mappers.

    This allows the system to automatically discover and use all
    available mappers without manual configuration.
    """

    _features: Dict[str, Type[BaseFeatureMapper]] = {}

    @classmethod
    def register_feature(cls, name: str, mapper_class: Type[BaseFeatureMapper]):
        """Register a feature mapper."""
        cls._features[name] = mapper_class

    @classmethod
    def get_mapper(cls, feature: str, version: str) -> BaseFeatureMapper:
        """Get a mapper instance for a specific feature and version."""
        if feature not in cls._features:
            raise ValueError(f"Unknown feature: {feature}")

        mapper_class = cls._features[feature]
        return mapper_class(version)

    @classmethod
    def get_all_mappers(cls, version: str) -> Dict[str, BaseFeatureMapper]:
        """Get all mapper instances for a specific version."""
        return {
            name: mapper_class(version)
            for name, mapper_class in cls._features.items()
        }
