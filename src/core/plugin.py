from __future__ import annotations

import discord

from abc import ABC, abstractmethod # Deprecated
from dataclasses import dataclass

from typing import TYPE_CHECKING, Awaitable, Callable, TypeVar
from logging import Logger

if TYPE_CHECKING:
    from .client import Bot
    from .sqlite import SQLiteDatabase
    from .config import ConfigManager
    from .plugin_manager import PluginManager

TService = TypeVar("TService")
TListener = TypeVar("TListener", bound=Callable[..., Awaitable[None]])

@dataclass(slots=True)
class PluginContext:
    """
    Base class for all plugin contexts.

    This class contains the context a plugin may use to function.
    """
    bot: Bot
    database: SQLiteDatabase
    config: ConfigManager
    plugin_manager: PluginManager
    logger: Logger

class Plugin(ABC):
    """
    Base class for all plugins.

    Subclasses override lifecycle hooks and use typed properties for framework access.
    """
    def __init__(self, context: PluginContext) -> None:
        super().__init__()
        self._context = context
        self._cog_names: list[str] = []
        self._listeners: list[tuple[str | None, Callable[..., Awaitable[None]]]] = []
    
    @property
    def bot(self) -> Bot:
        return self._context.bot
    
    @property
    def database(self) -> SQLiteDatabase:
        return self._context.database
    
    @property
    def config(self) -> ConfigManager:
        return self._context.config
    
    @property
    def plugin_manager(self) -> PluginManager:
        return self._context.plugin_manager
    
    @property
    def logger(self) -> Logger:
        return self._context.logger

    # @abstractmethod
    async def on_load(self) -> None:
        """Called after the plugin object is created."""

    # @abstractmethod
    async def on_enable(self) -> None:
        """Called when the plugin should register commands, listeners, cogs, or views."""

    # @abstractmethod
    async def on_disable(self) -> None:
        """Called during shutdown before the plugin is unloaded."""

    # @abstractmethod
    async def on_unload(self) -> None:
        """Called after disable for final cleanup."""

    def add_cog(self, cog: discord.Cog) -> None:
        self.bot.add_cog(cog)
        self._cog_names.append(cog.qualified_name)

    
    def listen(self, name: str | None = None) -> Callable[[TListener], TListener]:
        def decorator(func: TListener) -> TListener:
            listener = self.bot.listen(name=name)(func)
            self._listeners.append((name, listener))
            return listener
    
    def remove_registered_resources(self) -> None:
        for name, listener in self._listeners:
            self.bot.remove_listener(listener, name)
        self._listeners.clear()

        for cog_name in self._cog_names:
            self.bot.remove_cog(cog_name)
        self._cog_names.clear()

plugin = lambda context: Plugin(context)