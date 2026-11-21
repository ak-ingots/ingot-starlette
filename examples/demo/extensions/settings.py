"""The settings of the application: the configs of the addon and its own."""

__all__ = ("EchoConfigs", "EchoSettingsUnit")

from ingots.puer import Slot

from ingot_starlette.settings import StarletteSettingsUnit
from ingot_starlette.settings.configs import StarletteConfigs


class EchoConfigs(StarletteConfigs):
    """The configs of the application, beside those of the addon."""


class EchoSettingsUnit(StarletteSettingsUnit):
    configs = Slot(EchoConfigs)
