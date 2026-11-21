"""The logging of the application: the loggers of the addon and its own."""

__all__ = ("EchoLoggingUnit",)

from ingot_starlette.logging import StarletteLoggingUnit


class EchoLoggingUnit(StarletteLoggingUnit):
    """The loggers of the application, beside the logger of the addon."""
