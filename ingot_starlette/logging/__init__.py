"""The logging unit of the defaults with the logger of the addon."""

__all__ = ("StarletteLoggingUnit",)

import typing as t

from ingots.defaults.logging import LoggingUnit

if t.TYPE_CHECKING:
    from ..project import StarletteProject


class StarletteLoggingUnit(LoggingUnit):
    """
    The logging unit, with the logger of the addon, ``ingot_starlette``, at
    ``STARLETTE_LOGGING_LEVEL``.
    """

    project: "StarletteProject"

    @t.override
    def build_loggers(self) -> dict[str, dict[str, t.Any]]:
        level = self.project.settings.configs.STARLETTE_LOGGING_LEVEL
        addon = {"level": level, "handlers": ["default"], "propagate": False}
        return {**super().build_loggers(), "ingot_starlette": addon}
