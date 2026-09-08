import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import NotRequired, TypedDict

class BotConfigDict(TypedDict):
    command_prefix: str
    debug_guild_ids: list[int]
    message_content_intent: bool


class PluginConfigDict(TypedDict):
    enabled: NotRequired[bool]
    config: NotRequired[dict[str, object]]

@dataclass(slots=True)
class ProjectPaths:
    config_dir: Path = Path("config")
    data_dir: Path = Path("data")
    logs_dir: Path = Path("data/logs")
    database_file: Path = Path("data/database.db")
    main_config_file: Path = Path("config/config.json")
    plugins_config_file: Path = Path("config/plugins.json")

@dataclass(slots=True)
class BotConfig:
    command_prefix: str = "!"
    debug_guild_ids: list[int] = field(default_factory=list)
    message_content_intent: bool = False

@dataclass
class ConfigManager:
    """Small JSON configuration manager with typed core settings."""

    paths: ProjectPaths = field(default_factory=ProjectPaths)
    bot: BotConfig = field(default_factory=BotConfig)
    plugins: dict[str, PluginConfigDict] = field(default_factory=dict)

    def ensure_files(self) -> None:
        self.paths.config_dir.mkdir(parents=True, exist_ok=True)
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)

        if not self.paths.main_config_file.exists():
            self.save_main_config()
        else:
            self.load_main_config()

        if not self.paths.plugins_config_file.exists():
            self.save_plugins_config()
        else:
            self.load_plugins_config()

    def load_main_config(self) -> None:
        raw: dict = json.loads(self.paths.main_config_file.read_text(encoding="utf-8"))
        bot = raw.get("bot", {})
        if not isinstance(bot, dict):
            raise ValueError("config/config.json must contain a 'bot' object.")
        has_legacy_token = "token" in bot
        self.bot = BotConfig(
            command_prefix=str(bot.get("command_prefix", "!")),
            debug_guild_ids=[int(guild_id) for guild_id in bot.get("debug_guild_ids", [])],
            message_content_intent=bool(bot.get("message_content_intent", False)),
        )
        if has_legacy_token:
            self.save_main_config()
    
    def save_main_config(self) -> None:
        payload = {"bot": asdict(self.bot)}
        self.paths.main_config_file.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
    
    def load_plugins_config(self) -> None:
        raw = json.loads(self.paths.plugins_config_file.read_text(encoding="utf-8"))
        plugins = raw.get("plugins", {})
        if not isinstance(plugins, dict):
            raise ValueError("config/plugins.json must contain a 'plugins' object.")
        validated: dict[str, PluginConfigDict] = {}
        for plugin_name, plugin_config in plugins.items():
            if not isinstance(plugin_name, str):
                raise ValueError("Plugin names in config/plugins.json must be strings.")
            if not isinstance(plugin_config, dict):
                raise ValueError(f"Plugin config for {plugin_name!r} must be an object.")

            enabled = bool(plugin_config.get("enabled", True))
            config = plugin_config.get("config", {})
            if not isinstance(config, dict):
                raise ValueError(f"Plugin config for {plugin_name!r} must contain a config object.")
            validated[plugin_name] = {"enabled": enabled, "config": config}
        self.plugins = validated

    def save_plugins_config(self) -> None:
        payload = {"plugins": self.plugins}
        self.paths.plugins_config_file.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        plugin_config = self.plugins.get(plugin_name, {})
        return bool(plugin_config.get("enabled", True))

    def get_plugin_config(self, plugin_name: str) -> dict[str, object]:
        plugin_config = self.plugins.setdefault(plugin_name, {"enabled": True, "config": {}})
        config = plugin_config.setdefault("config", {})
        if not isinstance(config, dict):
            raise ValueError(f"Plugin config for {plugin_name!r} must be an object.")
        return config
    
    def ensure_plugin_defaults(
        self,
        plugin_name: str,
        default_config: dict[str, object],
    ) -> dict[str, object]:
        config = self.get_plugin_config(plugin_name)
        changed = False
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
                changed = True
        if changed:
            self.save_plugins_config()
        return config
