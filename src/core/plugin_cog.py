from abc import ABC
from discord import Cog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .plugin import Plugin

class PluginCog(ABC, Cog):
    """
    Base class for all plugin-based discord cogs.
    """
    def __init__(self, plugin: Plugin) -> None:
        self.plugin = plugin