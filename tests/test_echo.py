"""The echo of examples/demo: the endpoints, the policies, Starlette as it is."""

import typing as t
import unittest

from asgi import app
from project import EchoProject
from extensions.starlette import EchoStarletteUnit
from extensions.starlette.api import EchoApiUnit
from extensions.starlette.api.echo import EchoEndpoint
from ingots.puer import Slot
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from ingot_starlette.runner import StarletteRunner

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class EchoTestCase(unittest.TestCase):
    @t.override
    def setUp(self) -> None:
        self.client = self.enterContext(TestClient(app))

    def test_an_endpoint_answers_by_its_operation(self) -> None:
        response = self.client.post("/api/echo", json={"text": "hi"})
        self.assertEqual(response.json(), {"text": "hi"})
        self.assertEqual(self.client.get("/api/echo/there").json(), {"text": "there"})

    def test_a_failure_answers_by_its_policy(self) -> None:
        response = self.client.post("/api/fail", json={"text": "hi"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.headers["content-type"], "application/problem+json")
        problem = response.json()
        self.assertEqual(
            problem["type"], "https://echo.example.com/problems/echo-failed"
        )
        self.assertEqual(problem["detail"], "the echo of 'hi' failed, as asked")
        self.assertEqual(problem["text"], "hi")

    def test_the_errors_of_starlette_are_problems(self) -> None:
        response = self.client.get("/api/nope")
        self.assertEqual(
            response.json(),
            {"type": "about:blank", "status": 404, "title": "Not Found"},
        )
        response = self.client.get("/api/fail")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["allow"], "POST")

    def test_a_fault_is_an_internal_problem(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        with client, self.assertLogs("ingot_starlette", "ERROR"):
            response = client.post(
                "/api/echo",
                content=b"not json",
                headers={"content-type": "application/json"},
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"type": "about:blank", "status": 500, "title": "Internal Server Error"},
        )

    def test_starlette_as_it_is(self) -> None:
        response = self.client.post(
            "/api/echo",
            json={"text": "hi"},
            headers={"origin": "https://echo.example.com"},
        )
        self.assertEqual(
            response.headers["access-control-allow-origin"], "https://echo.example.com"
        )
        self.assertEqual(self.client.get("/version").text, "EchoProject 1.0")
        self.assertEqual(self.client.get("/health/").text, "ok")


class LoudEchoEndpoint(EchoEndpoint):
    """An extension: a route more, beside those of its base."""

    async def shout(self, request: Request) -> Response:
        return JSONResponse({"text": request.path_params["text"].upper()})

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield from super()._iter_routes()
        yield Route("/echo/{text}/loud", self.shout)


# a slot extends its base: a leaf replaced, each node above it too
class LoudApiUnit(EchoApiUnit):
    echo = Slot(LoudEchoEndpoint)


class LoudStarletteUnit(EchoStarletteUnit):
    api = Slot(LoudApiUnit)


class LoudProject(EchoProject):
    starlette = Slot(LoudStarletteUnit)


class TreeTestCase(unittest.TestCase):
    def test_the_routes_are_a_tree(self) -> None:
        with TestClient(StarletteRunner(EchoProject)) as client:
            runner = t.cast(StarletteRunner, client.app)
            self.assertEqual(runner.url_path_for("api:send"), "/api/echo")
            self.assertEqual(
                runner.url_path_for("api:send_path", text="hi"), "/api/echo/hi"
            )

    def test_an_extension_adds_a_route(self) -> None:
        with TestClient(StarletteRunner(LoudProject)) as client:
            self.assertEqual(client.get("/api/echo/hi/loud").json(), {"text": "HI"})
            self.assertEqual(client.get("/api/echo/hi").json(), {"text": "hi"})
