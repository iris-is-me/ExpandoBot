from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    priority: int = 100
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    default_config: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Plugin metadata requires a non-empty name.")
        if self.priority < 0:
            raise ValueError("Plugin priority must be 0 or greater.")

class PluginSource(str):
    BUILTIN = "BUILTIN"
    USER = "USER"