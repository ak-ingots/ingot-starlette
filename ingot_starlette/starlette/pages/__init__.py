"""The pages: the subtree of HTML, every path the API does not take."""

__all__ = ("StarlettePagesUnit",)

import typing as t

from ingots.puer import Slot

from ..errors import StarletteHtmlProblemRenderer
from ..subtrees import BaseStarletteSubtreeUnit


class StarlettePagesUnit(BaseStarletteSubtreeUnit):
    """
    The subtree of the pages, at the root, after the API: for a browser,
    its forms posted, its redirects, the pages a server renders. Its errors
    are pages of HTML, by :attr:`renderer`, the not found of every path no
    route takes among them; its pages in the slots of a subclass::

        class AppPagesUnit(StarlettePagesUnit):
            home = Slot(HomePage)

            @t.override
            def _iter_routes(self):
                yield from self.home.get_routes()
    """

    renderer = Slot(StarletteHtmlProblemRenderer)

    @t.override
    def _get_path(self) -> str:
        return ""
