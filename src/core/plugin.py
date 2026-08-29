import logging
import discord

from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger

from client import Bot

@dataclass(slots=True)
class PluginContext():
    """
    Base class for all plugin contexts.

    This class contains the context a plugin may use to function.
    """
    bot: Bot
    logger: Logger

class Plugin(ABC):
    """
    Base class for all plugins.

    Subclasses override lifecycle hooks and use typed properties for framework access.
    """
    def __init__(self, context: PluginContext) -> None:
        super().__init__()
        self._context = context
    
    @property
    def bot(self) -> Bot:
        return self._context.bot
    
    @property
    def logger(self) -> Logger:
        return self._context.logger

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
