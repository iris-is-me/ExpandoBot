import discord
import datetime
import logging
import socket
import aiohttp

from typing import TYPE_CHECKING, Callable, Awaitable

from .config import ConfigManager
from .sqlite import SQLiteDatabase

# Deprecated

import time
import asyncio
from pathlib import Path
from .plugin_manager import PluginManager

# Deprecated (End)

class Bot(discord.Bot):
    def __init__(
            self,
            config: ConfigManager,
            database: SQLiteDatabase,
            description = None,
            *args,
            **options
        ):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.database = database
        self.shutting_down = False
        self.listed_cogs: list[str] = []
        self.listed_listeners: list[tuple[str | None, Callable[..., Awaitable[None]]]] = []

        self.config.load_main_config()

        intents = self.get_intents_from_config()

        # Does this work?
        # @method
        # :(
        self._wait_until_bot_starts = self.wait_until_ready
        
        super().__init__(description, intents=intents, *args, **options)

    def get_intents_from_config(self) -> discord.Intents:
        self.logger.info("Fetching intents from config...")
        intents = discord.Intents()
        intents.presences = self.config.bot.presence_intent
        intents.message_content = self.config.bot.message_content_intent
        intents.members = self.config.bot.server_members_intent

        self.logger.info("Intents configured with members intent as %s, presences as %s, and messages as %s", intents.members, intents.presences, intents.message_content)
        return intents

    def add_cog(self, cog: discord.Cog, *, override: bool = False) -> None:
        self.listed_cogs.append(cog.qualified_name)
        return super().add_cog(cog, override=override)
    
    def remove_cog(self, name: str) -> discord.Cog | None:
        if name in self.listed_cogs:
            self.listed_cogs.remove(name)
        return super().remove_cog(name)

    def listen(self, name: str = discord.client.MISSING, once: bool = False) -> Callable[[discord.client.Coro], discord.client.Coro]:
        listener_func = super().listen(name, once=once)
        listener = tuple(name, listener_func)
        self.listed_listeners.append(listener)
        return listener_func

    def remove_listener(self, func: discord.client.Coro, name: str = discord.client.MISSING) -> None:
        listener = tuple(name, func)
        if listener in self.listed_listeners:
            self.listed_listeners.remove(listener)
        return super().remove_listener(func=func, name=name)
    
    @property
    def connect_time(self):
        try:
            return self._connect_time
        except:
            return None

    @property
    def first_connect_time(self):
        try:
            return self._first_connect_time
        except:
            return None        

    

    async def on_connect(self):
        await super().on_connect()
        now = datetime.datetime.now(datetime.timezone.utc)

        if  not hasattr(self, "connect_time") or self.connect_time is None:
            self._connect_time = now
            self._first_connect_time = self._connect_time
            self.logger.info("Connected to Discord")
        else:
            self._connect_time = now
            self.logger.info("Reconnected to Discord")
        
        self.logger.info("Connected as %s", self.user)

    async def close(self):
        self.close_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger.info(f"Client shutting down...")
        return await super().close()
    
    async def on_ready(self):
        self.ready_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger.info(f"Client ready")