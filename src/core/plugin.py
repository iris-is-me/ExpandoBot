import logging
import discord

from abc import ABC, abstractmethod


class Plugin(ABC):
    """
    Base class for all plugins.

    Subclasses override lifecycle hooks and use typed properties for framework access.
    """
    
    @abstractmethod
    async def on_load(self) -> None:
        """Called after the plugin object is created and migrations are available."""

    @abstractmethod
    async def on_enable(self) -> None:
        """Called when the plugin should register commands, listeners, cogs, or views."""

    @abstractmethod
    async def on_disable(self) -> None:
        """Called during shutdown before the plugin is unloaded."""

    @abstractmethod
    async def on_unload(self) -> None:
        """Called after disable for final cleanup."""
