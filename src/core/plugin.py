from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Awaitable, Callable, TypeVar
from logging import Logger

from .plugin_cog import PluginCog
from .datatypes import CogOperationResult

if TYPE_CHECKING:
    from .client import Bot
    from .sqlite import SQLiteDatabase
    from .config import ConfigManager
    from .plugin_manager import PluginManager

TService = TypeVar("TService") # Not used yet

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


class Plugin():
    """
    Base class for all plugins.

    A plugin is a class that has its own database, config and logger.

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
    
    @property
    def resource(self) -> dict:
        return {
            "cogs": self._cog_names,
            "listeners": self._listeners
        }

    async def on_load(self) -> None:
        """A coro method that is called after the plugin object is created.
        
        This method does not need to exist in your plugins. If this method does not exist in your plugin, it will simply skip the call.
        """

    async def on_enable(self) -> None:
        """A coro method that is called when the plugin should register commands, listeners, cogs, or views.
        
        This method does not need to exist in your plugins. If this method does not exist in your plugin, it will simply skip the call."""

    async def on_disable(self) -> None:
        """A coro method that is called before the plugin is unloaded.
        
        This method does not need to exist in your plugins. If this method does not exist in your plugin, it will simply skip the call."""

    async def on_unload(self) -> None:
        """A coro method that is called after disable for final cleanup.
        
        This method does not need to exist in your plugins. If this method does not exist in your plugin, it will simply skip the call."""

    def add_cog(
            self,
            cog: PluginCog,
            *,
            override: bool = False
        ) -> None:
        """Adds a "cog" to the bot. This method automatically provides the plugin object to the cog.

        A cog is a class that has its own event listeners and commands.

        Parameters
        ----------
        cog: :class:`PluginCog`
            The PluginCog class to register to the bot.

        override: :class:`bool`
            If a previously loaded cog with the same name should be ejected
            instead of raising an error.

        Raises
        ------
        TypeError
            The cog does not inherit from :class:`PluginCog`.
        ApplicationCommandError
            An error happened during loading.
        ClientException
            A cog with the same name is already loaded.
        """
        if not cog.qualified_name in self._cog_names:
            self._cog_names.append(cog.qualified_name)
        self.bot.add_cog(cog(self), override=override)

    def add_cogs(self, cogs: list[PluginCog], *, override: bool = False) -> None:
        """Adds a list of cogs to the bot. This method automatically provides the plugin object to each cog.

        A cog is a class that has its own event listeners and commands.

        Parameters
        ----------
        cog: :class:`list[PluginCog]`
            The list of cogs to register to the bot.

        override: :class:`bool`
            If a previously loaded cog with the same name should be ejected
            instead of raising an error.

        Raises
        ------
        TypeError
            The cog does not inherit from :class:`PluginCog`.
        ApplicationCommandError
            An error happened during loading.
        ClientException
            A cog with the same name is already loaded.
        """
        for cog in cogs:
            self.add_cog(cog, override=override)

    def remove_cog(self, cog: PluginCog | str) -> CogOperationResult:
        """Removes a cog from the bot and returns it.

        All registered commands and event listeners that the
        cog have registered will be removed as well.

        If the given cog does not exist then this method has no effect.

        Parameters
        ----------
        cog: :class:`list`[:class:`str` | :class:`PluginCog`]
            The cog to remove. The cog may be specified by its
            :class:`PluginCog` instance or its qualified name.

        Returns
        -------
        Optional[:class:`PluginCog`]
             The cog that was removed. ``None`` if not found.
        """
        success: bool = False
        cog_name: str = cog.qualified_name if isinstance(cog, PluginCog) else cog

        removed_cog = self.bot.remove_cog(cog_name)

        if TYPE_CHECKING:
            assert isinstance(removed_cog, PluginCog) or removed_cog == None, "The removed cog is not an instance of `PluginCog` or is not None" # Type hinting

        if removed_cog != None:
            removed_cog.remove_registered_resources()
            del self._cog_names[removed_cog.qualified_name]
            success = True

        state: CogOperationResult = CogOperationResult(
            cog = removed_cog,
            success = success
        )

        return state
    
    def remove_cogs(self, cogs: list[PluginCog | str]) -> list[PluginCog] :
        """
        Removes a list of cogs from the bot and returns the list of cog objects.

        All registered commands and event listeners that the
        cogs has registered will be removed as well.

        If no cogs is found then this method has no effect.

        Parameters
        ----------
        cog: list[:class:`str` | :class:`PluginCog`]
            The an iterable containing the cogs to remove. Each cog may be specified by its
            :class:`PluginCog` instance or its qualified name.

        Returns
        -------
        :class:`list[PluginCog]`
            The cogs that were successfully removed. Returns an empty
            list if none of the specified cogs were found.
        """
        removed_cogs: list[PluginCog] = []

        for cog in cogs:
            cog_name = cog.qualified_name if isinstance(cog, PluginCog) else cog
            removed_cog = self.remove_cog(cog_name).cog

            if removed_cog is not None:
                removed_cogs.append(removed_cog)

        return removed_cogs
    
    def remove_registered_resources(self) -> None:
        """
        Removes all registered resources of this plugin.
        """
        # Remove cogs
        self.remove_cogs(self._cog_names)
        self._cog_names.clear()

        # Remove plugin listeners
        for name, listener in self._listeners:
            self.bot.remove_listener(listener, name)
        self._listeners.clear()

plugin = lambda context: Plugin(context)