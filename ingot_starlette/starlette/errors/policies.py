"""The policies: an exception and the problem it answers."""

__all__ = (
    "BaseStarletteErrorPolicy",
    "BaseStaticStarletteErrorPolicy",
    "HttpStarletteErrorPolicy",
    "InternalStarletteErrorPolicy",
    "encode_problem",
)

import abc
import logging
import typing as t

from ingots.puer import Entity
from starlette.exceptions import HTTPException

from .data import StarletteProblem

if t.TYPE_CHECKING:
    from starlette.requests import HTTPConnection

logger = logging.getLogger(__name__)


class BaseStarletteErrorPolicy(Entity):
    """
    The policy of an exception, a strategy: the problem a request raising
    it answers with, by :meth:`encode`, and how it is logged, at
    :attr:`LOG_LEVEL`, with the traceback when :attr:`LOG_EXC_INFO`. It
    takes the exceptions of :attr:`EXCEPTION` and its subclasses, which
    Starlette finds by the MRO of an exception. What the problem looks like,
    JSON or HTML, is the renderer's of the subtree it is raised in.
    """

    EXCEPTION: t.ClassVar[type[Exception]]
    LOG_LEVEL: t.ClassVar[int] = logging.INFO
    LOG_EXC_INFO: t.ClassVar[bool] = False

    @t.final
    def report(
        self, error: Exception, connection: "HTTPConnection"
    ) -> StarletteProblem:
        """The problem of an exception of a connection, logged."""
        problem = self.encode(error)
        logger.log(
            self.LOG_LEVEL,
            "%s %s: %r, %s %s",
            connection.scope.get("method", "WS"),
            connection.url.path,
            error,
            problem.status,
            problem.type,
            exc_info=error if self.LOG_EXC_INFO else None,
        )
        return problem

    @abc.abstractmethod
    def encode(self, error: Exception) -> StarletteProblem:
        """The problem of an exception."""
        raise NotImplementedError


class BaseStaticStarletteErrorPolicy(BaseStarletteErrorPolicy):
    """
    A policy of one problem for every exception it takes, of :attr:`STATUS`,
    :attr:`TYPE` and :attr:`TITLE`, the text of the exception its detail::

        class InsufficientFundsPolicy(BaseStaticStarletteErrorPolicy):
            EXCEPTION = InsufficientFunds
            STATUS = 409
            TYPE = "https://shop.example.com/problems/insufficient-funds"
            TITLE = "Insufficient funds"
    """

    STATUS: t.ClassVar[int]
    TYPE: t.ClassVar[str] = "about:blank"
    TITLE: t.ClassVar[str] = ""

    @t.final
    @t.override
    def encode(self, error: Exception) -> StarletteProblem:
        return StarletteProblem(
            status=self.STATUS,
            type=self.TYPE,
            title=self.TITLE,
            detail=self._get_detail(error),
            extensions=self._get_extensions(error),
        )

    def _get_detail(self, error: Exception) -> str | None:
        """The detail of the problem: the text of the exception."""
        return str(error) or None

    def _get_extensions(self, error: Exception) -> t.Mapping[str, object]:
        """The extensions of the problem: none."""
        return {}


class InternalStarletteErrorPolicy(BaseStaticStarletteErrorPolicy):
    """
    Every exception no other policy takes: a fault of the server, its text
    kept from the client, logged at ``ERROR`` with its traceback. Starlette
    raises it on after the response, for the server to log it too.
    """

    EXCEPTION = Exception
    STATUS = 500
    TITLE = "Internal Server Error"
    LOG_LEVEL = logging.ERROR
    LOG_EXC_INFO = True

    @t.override
    def _get_detail(self, error: Exception) -> str | None:
        return None


class HttpStarletteErrorPolicy(BaseStarletteErrorPolicy):
    """
    The ``HTTPException`` of Starlette, of a route not found, 404, a method
    not allowed, 405, or of an endpoint: a problem of its status, its detail
    the title, its headers kept.
    """

    EXCEPTION = HTTPException

    @t.final
    @t.override
    def encode(self, error: Exception) -> StarletteProblem:
        error = t.cast(HTTPException, error)
        return StarletteProblem(
            status=error.status_code,
            title=error.detail,
            headers=error.headers or {},
        )


def encode_problem(problem: StarletteProblem) -> dict[str, object]:
    """The body of a problem, as JSON encodes it."""
    body: dict[str, object] = {"type": problem.type, "status": problem.status}
    if problem.title:
        body["title"] = problem.title
    if problem.detail is not None:
        body["detail"] = problem.detail
    body.update(problem.extensions)
    return body
