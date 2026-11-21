"""The renderers: a problem as the response of a subtree, JSON or HTML."""

__all__ = (
    "BaseStarletteProblemRenderer",
    "StarletteHtmlProblemRenderer",
    "StarletteJsonProblemRenderer",
)

import abc
import html
import json
import typing as t

from ingots.puer import Entity
from starlette.responses import HTMLResponse, Response
from starlette.websockets import WebSocket, WebSocketState

from .policies import encode_problem

if t.TYPE_CHECKING:
    from starlette.requests import HTTPConnection

    from .data import StarletteProblem

PROBLEM_CONTENT_TYPE: t.Final = "application/problem+json"
_PROBLEM_CODES: t.Final = 4000  # the close of a WebSocket: + the status, 4409


class BaseStarletteProblemRenderer(Entity):
    """
    The renderer of the problems of a subtree, a strategy: a request answers
    with :meth:`_render_response`; a WebSocket not accepted is refused by
    it, one accepted gets :meth:`_render_message` and is closed by ``4000 +
    status``. The policy tells the problem, the renderer its form; the
    connection is the context beside it, for a template its links, its
    caller, its language.
    """

    @t.final
    async def render(
        self, problem: "StarletteProblem", connection: "HTTPConnection"
    ) -> Response | None:
        """The response of a problem, or the close of a WebSocket."""
        response = self._render_response(problem, connection)
        if not isinstance(connection, WebSocket):
            return response
        if connection.application_state == WebSocketState.CONNECTED:
            await connection.send_text(self._render_message(problem, connection))
            await connection.close(_PROBLEM_CODES + problem.status)
        else:
            await connection.send_denial_response(response)
        return None

    @abc.abstractmethod
    def _render_response(
        self, problem: "StarletteProblem", connection: "HTTPConnection"
    ) -> Response:
        raise NotImplementedError

    def _render_message(
        self, problem: "StarletteProblem", connection: "HTTPConnection"
    ) -> str:
        """The message of a WebSocket: ``{"problem": ...}``."""
        return json.dumps({"problem": encode_problem(problem)})


class StarletteJsonProblemRenderer(BaseStarletteProblemRenderer):
    """A problem as ``application/problem+json``, of RFC 9457."""

    @t.final
    @t.override
    def _render_response(
        self, problem: "StarletteProblem", connection: "HTTPConnection"
    ) -> Response:
        return Response(
            json.dumps(encode_problem(problem)),
            status_code=problem.status,
            headers=dict(problem.headers),
            media_type=PROBLEM_CONTENT_TYPE,
        )


class StarletteHtmlProblemRenderer(BaseStarletteProblemRenderer):
    """
    A problem as a page of HTML, its title and detail, escaped; a subclass
    gives a page of its own by :meth:`_render_page`, a template of the
    problem and of the request, its links, its caller::

        class AppHtmlProblemRenderer(StarletteHtmlProblemRenderer):
            @t.override
            def _render_page(self, problem, connection):
                template = templates.get_template(f"errors/{problem.status}.html")
                return template.render(problem=problem, request=connection)
    """

    @t.final
    @t.override
    def _render_response(
        self, problem: "StarletteProblem", connection: "HTTPConnection"
    ) -> Response:
        return HTMLResponse(
            self._render_page(problem, connection),
            status_code=problem.status,
            headers=dict(problem.headers),
        )

    def _render_page(
        self, problem: "StarletteProblem", connection: "HTTPConnection"
    ) -> str:
        """The page of a problem: a minimal one, of no link."""
        title = html.escape(problem.title or str(problem.status))
        detail = f"<p>{html.escape(problem.detail)}</p>" if problem.detail else ""
        return (
            "<!doctype html>"
            f"<html><head><title>{problem.status} {title}</title></head>"
            f"<body><h1>{title}</h1>{detail}</body></html>"
        )
