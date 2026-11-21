"""
ingot-starlette: Integration of Starlette, the ASGI framework, into Ingots
applications. An application inherits from :class:`StarletteProject`, or
joins the units of the addon, ``settings``, ``logging`` and ``starlette``,
with those of its other addons.
"""

__all__ = ("StarletteProject",)

from .project import StarletteProject
