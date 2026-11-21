"""The settings unit of the defaults with the configs of the addon."""

__all__ = ("StarletteSettingsUnit",)

from ingots.defaults.settings import SettingsUnit
from ingots.puer import Slot

from .configs import StarletteConfigs


class StarletteSettingsUnit(SettingsUnit):
    """The settings unit, with the addon's :class:`StarletteConfigs`."""

    configs = Slot(StarletteConfigs)
