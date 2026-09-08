import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Awaitable, Callable

from .sqlite import SQLiteDatabase


MigrationCallable = Callable[[SQLiteDatabase], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Migration:
    plugin_name: str
    version: str
    path: Path
    module: ModuleType
    up: MigrationCallable
    down: MigrationCallable


class MigrationRunner:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    async def ensure_table(self) -> None:
        await self.database.execute(
            """
            CREATE TABLE IF NOT EXISTS plugin_migrations (
                plugin_name TEXT NOT NULL,
                version TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (plugin_name, version)
            )
            """
        )

    async def run_up(self, plugin_name: str, migrations_dir: Path) -> None:
        await self.ensure_table()
        for migration in self.discover(plugin_name, migrations_dir):
            if await self._is_applied(plugin_name, migration.version):
                continue
            await migration.up(self.database)
            await self.database.execute(
                "INSERT INTO plugin_migrations (plugin_name, version) VALUES (?, ?)",
                (plugin_name, migration.version),
            )

    async def run_down(self, plugin_name: str, migrations_dir: Path) -> None:
        await self.ensure_table()
        migrations = list(reversed(self.discover(plugin_name, migrations_dir)))
        for migration in migrations:
            if not await self._is_applied(plugin_name, migration.version):
                continue
            await migration.down(self.database)
            await self.database.execute(
                "DELETE FROM plugin_migrations WHERE plugin_name = ? AND version = ?",
                (plugin_name, migration.version),
            )

    def discover(self, plugin_name: str, migrations_dir: Path) -> list[Migration]:
        if not migrations_dir.exists():
            return []

        migrations: list[Migration] = []
        for path in sorted(migrations_dir.glob("[0-9][0-9][0-9]_*.py")):
            module = self._import_migration(plugin_name, path)
            up = getattr(module, "up", None)
            down = getattr(module, "down", None)
            if not callable(up) or not callable(down):
                raise TypeError(f"{path} must define async up(db) and async down(db).")
            if not inspect.iscoroutinefunction(up) or not inspect.iscoroutinefunction(down):
                raise TypeError(f"{path} up and down functions must be async.")
            migrations.append(
                Migration(
                    plugin_name=plugin_name,
                    version=path.stem.split("_", maxsplit=1)[0],
                    path=path,
                    module=module,
                    up=up,
                    down=down,
                )
            )
        return migrations

    async def _is_applied(self, plugin_name: str, version: str) -> bool:
        row = await self.database.fetch_one(
            "SELECT 1 FROM plugin_migrations WHERE plugin_name = ? AND version = ?",
            (plugin_name, version),
        )
        return row is not None

    def _import_migration(self, plugin_name: str, path: Path) -> ModuleType:
        module_name = f"expandobot_migration_{plugin_name}_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not import migration {path}.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
