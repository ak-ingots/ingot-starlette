"""
Starlette in the application: its three subtrees, the API of JSON at
``/api``, the WebSockets at ``/ws`` and the pages of HTML, each with its
endpoints or resources; the policies of
the errors, shared, each subtree rendering them its own way.
"""

__all__ = ("EchoStarletteUnit",)

from ingots.puer import Slot

from ingot_starlette.starlette import StarletteUnit

from .api import EchoApiUnit
from .errors import EchoStarletteErrorsUnit
from .pages import EchoPagesUnit
from .ws import EchoWebSocketsUnit


class EchoStarletteUnit(StarletteUnit):
    errors = Slot(EchoStarletteErrorsUnit)
    api = Slot(EchoApiUnit)
    ws = Slot(EchoWebSocketsUnit)
    pages = Slot(EchoPagesUnit)
