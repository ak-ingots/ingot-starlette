"""
Starlette in the application: its two subtrees, the API of JSON at
``/api`` and the pages of HTML, each with its endpoints; the policies of
the errors, shared, each subtree rendering them its own way.
"""

__all__ = ("EchoStarletteUnit",)

from ingots.puer import Slot

from ingot_starlette.starlette import StarletteUnit

from .api import EchoApiUnit
from .errors import EchoStarletteErrorsUnit
from .pages import EchoPagesUnit


class EchoStarletteUnit(StarletteUnit):
    errors = Slot(EchoStarletteErrorsUnit)
    api = Slot(EchoApiUnit)
    pages = Slot(EchoPagesUnit)
