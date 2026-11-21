"""The configs of the addon, named ``STARLETTE_*``."""

__all__ = ("StarletteConfigs",)

import logging

from ingots.defaults.settings.configs import BoolConfig, Configs, LogLevelConfig


class StarletteConfigs(Configs):
    """The configs of the defaults with those of the addon."""

    STARLETTE_LOGGING_LEVEL = LogLevelConfig(logging.INFO)
    # the tracebacks of the failed requests in their responses: never in production
    STARLETTE_IS_DEBUG = BoolConfig(False)
