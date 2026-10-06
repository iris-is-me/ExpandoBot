# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - [Unreleased]
### Added
- Added some licensing info in the [package metadata module](__init__.py)
- Added a custom Discord Cog definition that accepts the plugin itself as an argument.
- Added support for bulk Cog loading.
- Added support for Cog unloading.
- Added support for bulk Cog unloading.
- Added docstrings for cog loading and unloading.
- Added an internet check.
- Added a field in Plugin Metadata dataclass to support pip dependencies for plugins

### Changed
- Changed `kernel.py` to inherit separation of responsibilities.
- Changed repository security details to include the MINOR as `x`, in terms of Semantic Versioning.
- Changed plugin management to own plugin startup and shutdown operations

### Removed
- Removed abstracting of plugin events. Each event can be skipped if not defined

## [0.1.0] - 2026-9-8

### Added
- Added `CHANGELOG.md` for documenting project changes.
- Added `NOTICE` for project notices.
- Added `README.md` for project documentation.
- Added `ROADMAP.md` for the project roadmap.
- Added `SECURITY.md` for documenting the project's security policy and vulnerability reporting process.
- Added `/docs` for documentation of this project.

- Added `main.py` as the application entry point.
- Added `kernel.py` for bot initialization and lifecycle management.
- Added `client.py` for bot client definition.
- Added `plugin.py` for plugin definitions.
- Added `plugin_manager.py` for plugin instance management.
- Added `plugin_discovery.py` for plugin discovery.
- Added `plugin_metadata.py` for plugin specs.
- Added `sqlite.py` for SQL interface.
- Added `migrations.py` for SQL interface.
- Added `config.py` for token fetching.
- Added `lifecycle.py` for managing shutdown.
- Added `prerun.py` for prerunning before bot is initialsed.
- Added `requirements.txt` for project dependencies.

### Changed
- Changed `LICENSE` to include copyright owner
- Changed `SECURITY.md` to contain security reporting instructions

## [0.0.0] - 2026-07-1

### Added
- Added `LICENSE` file based on Apache 2.0.