"""The runner: the application of Starlette, the project inside."""

__all__ = ("StarletteRunner",)

import logging
import typing as t
from dataclasses import dataclass

from ingots.defaults import ProjectCliArgs
from ingots.puer import UserError
from starlette.applications import Starlette

if t.TYPE_CHECKING:
    from starlette.middleware import Middleware
    from starlette.routing import BaseRoute
    from starlette.types import ExceptionHandler, Receive, Scope, Send

    from .project import StarletteProject

logger = logging.getLogger(__name__)


class StarletteRunner(Starlette):
    """
    The application of Starlette an ASGI server imports, the project inside,
    as a runner of commands runs one: the lifespan of the server configures
    the project at the startup and shuts it down at the shutdown. Configured,
    the project gives the application its routes, its middleware and its
    handlers of exceptions, by ``project.starlette``; the server owns the
    process, its event loop and its signals: ``uvicorn app.asgi:app
    --workers 4`` runs a project in each worker::

        app = StarletteRunner(AppProject)

    What the application is given as Starlette's, before its first startup,
    stays: the routes of ``add_route`` and ``mount`` come before those of
    the project, the middleware of ``add_middleware`` outside them, the
    handlers of ``add_exception_handler`` over the policies, ``debug`` on if
    set here or by ``STARLETTE_IS_DEBUG``::

        app = StarletteRunner(AppProject)
        app.add_route("/", homepage)
        app.add_middleware(GZipMiddleware)

    The configs come from the environment, and from ``cli_args`` as the
    command line gives them to a project run by commands. The endpoints reach
    the project by their entities, or, a function, by ``request.app.project``.
    The lifespan is the project's: the lifespans of Starlette, of a mounted
    application too, do not run.
    """

    _own: "_Own"

    def __init__(
        self,
        project_cls: type["StarletteProject"],
        cli_args: ProjectCliArgs = ProjectCliArgs(),
    ) -> None:
        super().__init__()
        self._project_cls = project_cls
        self._cli_args = cli_args
        self._project: "StarletteProject | None" = None

    @t.final
    @property
    def project(self) -> "StarletteProject":
        """
        The running project.

        :raises RuntimeError: no lifespan started it: the server runs none.
        """
        if self._project is None:
            raise RuntimeError(f"{type(self).__qualname__}: no project is running")
        return self._project

    @t.final
    @t.override
    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["type"] == "lifespan":
            await self._serve_lifespan(receive, send)
            return
        self.project  # no request before the lifespan has started the project
        await super().__call__(scope, receive, send)

    @t.final
    async def _serve_lifespan(self, receive: "Receive", send: "Send") -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    await self._start()
                except Exception as error:
                    await send(
                        {"type": "lifespan.startup.failed", "message": repr(error)}
                    )
                    raise  # as Starlette's lifespan: the server stops on both
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await self._stop()
                await send({"type": "lifespan.shutdown.complete"})
                return

    @t.final
    async def _start(self) -> None:
        project = self._project_cls()
        project._cli_set_args(self._cli_args)
        try:
            await project._configure()
        except Exception as error:
            if isinstance(error, UserError):
                logger.error("configuring failed: %s", error)
            else:
                logger.exception("configuring failed: %r", error)
            await project._do_shut_down()
            raise
        own, starlette = self._get_own(), project.starlette
        self.router.routes = [*own.routes, *starlette.get_routes()]
        self.user_middleware = [*own.middleware, *starlette.get_middleware()]
        self.exception_handlers = {
            **starlette.errors.get_exception_handlers(),
            **own.exception_handlers,
        }
        self.debug = own.debug or project.settings.configs.STARLETTE_IS_DEBUG
        self.middleware_stack = None  # built anew, of this project, at the first call
        self._project = project

    @t.final
    def _get_own(self) -> "_Own":
        # what the application was given as Starlette's, before the first
        # startup: each startup builds on it, not on the last project's
        try:
            return self._own
        except AttributeError:
            pass
        self._own = _Own(
            routes=tuple(self.router.routes),
            middleware=tuple(self.user_middleware),
            exception_handlers=dict(self.exception_handlers),
            debug=self.debug,
        )
        return self._own

    @t.final
    async def _stop(self) -> None:
        project, self._project = self._project, None
        if project is None:
            return
        try:
            await project._do_shut_down()
        except Exception as error:
            logger.exception("shutting down failed: %r", error)


@dataclass(frozen=True, slots=True, kw_only=True)
class _Own:
    routes: "tuple[BaseRoute, ...]"
    middleware: "tuple[Middleware, ...]"
    exception_handlers: "dict[t.Any, ExceptionHandler]"
    debug: bool
