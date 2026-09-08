import importlib.util
import sys
import inspect

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from types import ModuleType

from .plugin_metadata import PluginMetadata, PluginSource
from .plugin import PluginContext, Plugin

PluginFactory = Callable[[PluginContext], Plugin]

@dataclass(frozen=True, slots=True)
class PluginDescriptor:
    metadata: PluginMetadata
    source: PluginSource
    root: Path
    module: ModuleType
    factory: PluginFactory


def discover_plugins(root: Path, source: PluginSource) -> list[PluginDescriptor]:
    if not root.exists():
        return []

    descriptors: list[PluginDescriptor] = []
    for candidate in sorted(path for path in root.iterdir() if path.is_dir()):
        plugin_file = candidate / "plugin.py"
        print(plugin_file.absolute())
        if not plugin_file.exists():
            continue
        descriptors.append(_load_descriptor(candidate, plugin_file, source))
    return descriptors


def _load_descriptor(root: Path, plugin_file: Path, source: PluginSource) -> PluginDescriptor:
    module_name = f"expandobot_{source}_{root.name}_plugin"

    spec = importlib.util.spec_from_file_location(
        module_name,
        plugin_file,
        submodule_search_locations=[str(root)],
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for {plugin_file}.")

    module = importlib.util.module_from_spec(spec)

    # Make the package information explicit.
    module.__package__ = module_name

    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise

    metadata = getattr(module, "metadata", None)
    if not isinstance(metadata, PluginMetadata):
        raise TypeError(f"{plugin_file} must define 'metadata: PluginMetadata'.")

    factory = getattr(module, "plugin", None)
    if not callable(factory):
        raise TypeError(f"{plugin_file} must define callable 'plugin(context)'.")

    signature = inspect.signature(factory)
    if len(signature.parameters) != 1:
        raise TypeError(f"{plugin_file} 'plugin' must accept exactly one context argument.")

    return PluginDescriptor(
        metadata=metadata,
        source=source,
        root=root,
        module=module,
        factory=factory,
    )
