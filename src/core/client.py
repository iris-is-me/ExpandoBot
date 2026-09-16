import discord
import datetime
import logging
import time
import asyncio

from pathlib import Path
from typing import TYPE_CHECKING

from .config import ConfigManager
from .sqlite import SQLiteDatabase
from .plugin_manager import PluginManager


class Bot(discord.Bot):
    def __init__(self, description=None, *args, **options):
        self.logger = logging.getLogger(__name__)
        self.config = ConfigManager()
        self.database = SQLiteDatabase(self.config.paths.database_file)
        self.plugin_manager = PluginManager(
            bot=self,
            config=self.config,
            database=self.database,
            builtin_plugins_dir=Path("builtin_plugins"),
            user_plugins_dir=Path("plugins"),
        )
        self.shutting_down = False
        self._plugins_started = False

        super().__init__(description, *args, **options)

    async def _start_plugins(self) -> None:
        if self._plugins_started:
            self.logger.debug("Skipping plugin initialisation as plugins are already loaded")
            return
        await self.plugin_manager.discover_and_load_all()
        await self.plugin_manager.enable_all()
        self._plugins_started = True

    async def _end_plugins(self) -> None:
        if not self._plugins_started:
            self.logger.debug("Skipping plugin unloading as plugins are already unloaded")
            return
        await self.plugin_manager.disable_all()
        await self.plugin_manager.unload_all()
        self._plugins_started = False

    async def on_connect(self):
        await self.database.connect()
        await self._start_plugins()
        await super().on_connect()
        now = datetime.datetime.now(datetime.timezone.utc)

        if  not hasattr(self, "connect_time") or self.connect_time is None:
            self.connect_time = now
            self.last_connect_time = self.connect_time
            self.logger.info("Connected to Discord")
        else:
            self.last_connect_time = now
            self.logger.info("Reconnected to Discord")
        
        self.logger.info("Connected as %s", self.user)

    async def close(self):
        self.close_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger.info(f"Client shutting down")
        await self._end_plugins()
        await self.database.close()
        return await super().close()
    
    async def on_ready(self):
        self.ready_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger.info(f"Client ready")