"""The subtrees of the application: a mount each, its middleware and errors."""

__all__ = ("BaseStarletteSubtreeUnit",)

import abc
import typing as t

from ingots.puer import Slot, Unit
from starlette.middleware import Middleware
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.routing import Mount

from .endpoints import StarletteEndpoint
from .errors import BaseStarletteProblemRenderer

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from ingot_starlette.project import StarletteProject


class BaseStarletteSubtreeUnit(StarletteEndpoint, Unit):
    """
    A subtree of the application, a node of the routes the Starlette unit
    mounts at :meth:`_get_path`: its endpoints in its slots, its routes those
    of :meth:`_iter_routes`, its middleware those of :meth:`_iter_middleware`,
    of Starlette as they are, and its errors its own: the policies of
    ``starlette.errors`` rendered by its :attr:`renderer`, a not found, a
    method not allowed, a fault of its endpoints alike. The kinds of the
    subtrees, :class:`~ingot_starlette.starlette.api.StarletteApiUnit` and
    :class:`~ingot_starlette.starlette.pages.StarlettePagesUnit`, check what
    they take by :meth:`_iter_guards`.
    """

    project: "StarletteProject"

    renderer = Slot(BaseStarletteProblemRenderer)  # type: ignore[type-abstract]

    @t.final
    def get_mount(self) -> Mount:
        """The mount of the subtree, its routes inside its middleware."""
        errors = self.project.starlette.errors
        handlers = errors.get_exception_handlers(self.renderer)
        middleware = [
            *self._iter_middleware(),
            Middleware(ExceptionMiddleware, handlers=handlers),
            *self._iter_guards(),
        ]
        return Mount(
            self._get_path(),
            routes=self.get_routes(),
            middleware=middleware,
            name=self._get_name(),
        )

    @abc.abstractmethod
    def _get_path(self) -> str:
        """The path of the mount: ``""`` the root."""
        raise NotImplementedError

    def _get_name(self) -> str | None:
        """The name of the mount, of ``url_path_for("<name>:<route>")``: none."""
        return None

    def _iter_middleware(self) -> "Iterator[Middleware]":
        """
        The middleware of the subtree, the outermost first, outside its
        errors: none here. A subclass adding to those of its base yields them
        too.
        """
        return iter(())

    def _iter_guards(self) -> "Iterator[Middleware]":
        """
        The middleware checking what the subtree takes, inside its errors, so
        that a refusal, an ``HTTPException``, answers by them: none here.
        """
        return iter(())
