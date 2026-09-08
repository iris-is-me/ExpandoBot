from __future__ import annotations

import logging


from pathlib import Path
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:from .client import Bot
from .plugin import Plugin, PluginContext

from .config import ConfigManager
from .plugin_discovery import PluginDescriptor, discover_plugins, PluginSource


from .sqlite import SQLiteDatabase
from .migrations import MigrationRunner


@dataclass(slots=True)
class LoadedPlugin:
    descriptor: PluginDescriptor
    instance: Plugin
    enabled: bool = False

class PluginManager:
    """A plugin manager that discovers, orders, loads, enables, disables, and unloads plugins."""

    def __init__(
        self,
        bot: Bot,
        database: SQLiteDatabase,
        config: ConfigManager,
        builtin_plugins_dir: Path,
        user_plugins_dir: Path,
        ):
        self.bot = bot
        self.database = database
        self.config = config
        self.builtin_plugins_dir = builtin_plugins_dir
        self.user_plugins_dir = user_plugins_dir
        self.logger = logging.getLogger(__name__)
        self.plugin_loggers: dict[str, logging.Logger] = {}
        self._loaded: dict[str, LoadedPlugin] = {}

    @property
    def loaded_plugins(self) -> dict[str, LoadedPlugin]:
        return dict(self._loaded)
    
    # Loading

    async def discover_and_load_all(self) -> None:
        plugins = []
        builtin = discover_plugins(self.builtin_plugins_dir, PluginSource.BUILTIN)
        user = discover_plugins(self.user_plugins_dir, PluginSource.USER)
        plugins.extend(builtin)
        plugins.extend(user)
        if not plugins:
            self.logger.warning("No plugins found")
            return

        for descriptor in self._order_group(plugins):
            if not self.config.is_plugin_enabled(descriptor.metadata.name):
                self.logger.info("Skipping disabled plugin %s", descriptor.metadata.name)
                continue
            await self.load(descriptor)

    async def load(self, descriptor: PluginDescriptor) -> None:
        metadata = descriptor.metadata
        if metadata.name in self._loaded:
            raise ValueError(f"Duplicate plugin name: {metadata.name}")
        
        missing = [name for name in metadata.dependencies if name not in self._loaded]
        if missing:
            missing_text = "\n - ".join(missing)
            raise RuntimeError(f"Plugin {metadata.name} is missing dependencies: {missing_text}")
        
        self.config.ensure_plugin_defaults(metadata.name, metadata.default_config)
        plugin_logger = logging.getLogger(f"plugins.{metadata.name}")
        self.plugin_loggers[metadata.name] = plugin_logger
        context = PluginContext(
            bot=self.bot,
            database=self.database,
            config=self.config,
            plugin_manager=self,
            logger=plugin_logger,
        )

        migration_runner = MigrationRunner(self.database)
        await migration_runner.run_up(metadata.name, descriptor.root / "migrations")

        instance = descriptor.factory(context)
        self._loaded[metadata.name] = LoadedPlugin(descriptor=descriptor, instance=instance)
        await instance.on_load()
        self.logger.info(
            "Loaded %s plugin %s v%s",
            descriptor.source.lower(),
            metadata.name,
            metadata.version,
        )

    # Enabling

    async def enable_all(self) -> None:
        for name in list(self._loaded):
            await self.enable(name)

    async def enable(self, plugin_name: str) -> None:
        loaded = self._loaded[plugin_name]
        if loaded.enabled:
            return
        await loaded.instance.on_enable()
        loaded.enabled = True
        self.logger.info("Enabled plugin %s", plugin_name)
    
    # Disabling

    async def disable_all(self) -> None:
        self.logger.info("Disabing all loaded plugins")
        for name in reversed(list(self._loaded)):
            await self.disable(name)

    async def disable(self, plugin_name: str) -> None:
        loaded = self._loaded[plugin_name]
        if not loaded.enabled:
            return
        await loaded.instance.on_disable()
        loaded.instance.remove_registered_resources()
        loaded.enabled = False
        self.logger.info("Disabled plugin %s", plugin_name)

    # Unloading
    
    async def unload_all(self) -> None:
        self.logger.info("Unloading all loaded plugins")
        for name in reversed(list(self._loaded)):
            await self.unload(name)

    async def unload(self, plugin_name: str) -> None:
        loaded = self._loaded[plugin_name]
        if loaded.enabled:
            await self.disable(plugin_name)
        await loaded.instance.on_unload()
        await loaded.instance.database.close()
        del self._loaded[plugin_name]
        self.logger.info("Unloaded plugin %s", plugin_name)

    # Helpers
    
    def is_loaded(self, plugin_name: str) -> bool:
        return plugin_name in self._loaded
    
    def get_plugin(self, plugin_name: str) -> Plugin:
        try:
            return self._loaded[plugin_name].instance
        except KeyError as exc:
            raise LookupError(f"Plugin is not loaded: {plugin_name}") from exc
        
    def _order_group(self, descriptors: list[PluginDescriptor]) -> list[PluginDescriptor]:
        by_name = {descriptor.metadata.name: descriptor for descriptor in descriptors}
        for descriptor in descriptors:
            missing = [
                dependency
                for dependency in descriptor.metadata.dependencies
                if dependency not in self._loaded and dependency not in by_name
            ]
            if missing:
                missing_text = ", ".join(missing)
                raise RuntimeError(
                    f"Plugin {descriptor.metadata.name} is missing dependencies: {missing_text}"
                )
            
        ordered: list[PluginDescriptor] = []
        pending = set(by_name)

        while pending:
            ready = [
                by_name[name]
                for name in pending
                if all(
                    dep in self._loaded or dep in by_name and dep not in pending
                    for dep in by_name[name].metadata.dependencies
                )
            ]
            if not ready:
                blocked = ", ".join(sorted(pending))
                raise RuntimeError(f"Plugin dependency cycle or missing dependency inside group: {blocked}")

            ready.sort(key=lambda descriptor: descriptor.metadata.priority)
            for descriptor in ready:
                ordered.append(descriptor)
                pending.remove(descriptor.metadata.name)

        return ordered
