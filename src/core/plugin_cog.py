from abc import ABC
from discord import Cog
from typing import TYPE_CHECKING, Awaitable, Callable, TypeVar

if TYPE_CHECKING:
    from .plugin import Plugin

TListener = TypeVar("TListener", bound=Callable[..., Awaitable[None]])

class PluginCog(Cog):
    """
    Base class for all plugin-based discord cogs must inherit from.

    A cog is a collection of commands, listeners, and optional state to
    help group commands together.

    Parameters
    ----------
    plugin: :class:`.plugin.Plugin`
        The plugin that registered the cog. This may be used by the cog itself to function.
    """
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin
        self._listeners: list[tuple[str | None, Callable[..., Awaitable[None]]]] = []
    
    def listen(self, name: str | None = None) -> Callable[[TListener], TListener]:
        """Register a function as a bot event listener.

        This is a wrapper around the bot's :meth:`listen` decorator that also
        tracks the registered listener so it can be managed by the plugin.
    
        Parameters
        ----------
        name:
            The name of the event to listen for. If omitted, the decorated
            function's name is used.
    
        Returns
        -------
        Callable[[TListener], TListener]
            A decorator that registers and returns the listener function.
        """
        def decorator(func: TListener) -> TListener:
            listener = self.plugin.bot.listen(name=name)(func)
            self._listeners.append((name, listener))
            return listener
        return decorator
    
    def remove_registered_resources(self):
        for name, listener in self._listeners:
            self.plugin.bot.remove_listener(listener, name)
        self._listeners.clear()
