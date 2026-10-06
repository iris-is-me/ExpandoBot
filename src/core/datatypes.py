from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .plugin_cog import PluginCog

@dataclass
class CogOperationResult:
    """
    Dataclass that contains a state of a cog operation

    Parameters
    ----------
    cog: :class:`PluginCog`
        The cog that was operated on.

    success: :class:`bool`
        Whether the operation was a sucess

    Returns
    -------
    :class:`CogOperationResult`[`cog`, `success`]
        Returns both the cog that was operated and
        whether the operation was a sucess.

    :var:`cog`
        If called, returns the cog that was operated

    Usage
    -----
    .. code-block:: python3

        state: CogOperationResult = CogOperationResult(
            cog = cog,
            success = success
        )
        return state

        # In some other file

        cog = state()               # Returns the cog

        success = state.success     # Returns whether the operation was a sucess
        cog = state.cog             # Returns the cog, again

    """
    cog: PluginCog | None
    success: bool

    def __call__(self) -> PluginCog | None:
        return self.cog