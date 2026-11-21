"""The project of the addon: what an application inherits from."""

__all__ = ("StarletteProject",)

from ingots.defaults import Project
from ingots.puer import Slot

from .logging import StarletteLoggingUnit
from .settings import StarletteSettingsUnit
from .starlette import StarletteUnit


class StarletteProject(Project):
    """
    The project of the defaults with the addon's
    :class:`StarletteSettingsUnit`, :class:`StarletteLoggingUnit` and
    Starlette, :class:`StarletteUnit`. An application inherits from it and
    sets its own ``env_configs_prefix``; the addon run on its own
    (``python -m ingot_starlette``) keeps the prefix of the defaults,
    ``INGOT``.
    """

    settings = Slot(StarletteSettingsUnit)
    logging = Slot(StarletteLoggingUnit)
    starlette = Slot(StarletteUnit)
