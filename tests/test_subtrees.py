"""The two subtrees of the demo: the API of JSON alone, the pages of HTML."""

import typing as t
import unittest

from asgi import app
from project import EchoProject
from extensions.starlette import EchoStarletteUnit
from extensions.starlette.pages import EchoPagesUnit
from ingots.puer import Slot
from starlette.requests import HTTPConnection
from starlette.testclient import TestClient

from ingot_starlette.runner import StarletteRunner
from ingot_starlette.starlette.api.guards import accepts_json, is_json
from ingot_starlette.starlette.errors import (
    StarletteHtmlProblemRenderer,
    StarletteProblem,
)

HTML: t.Final = "text/html; charset=utf-8"
PROBLEM: t.Final = "application/problem+json"


class ApiTestCase(unittest.TestCase):
    @t.override
    def setUp(self) -> None:
        self.client = self.enterContext(TestClient(app))

    def test_an_accept_of_no_json_is_refused(self) -> None:
        for accept in ("text/html", "application/xml", "application/json;q=0"):
            with self.subTest(accept=accept):
                response = self.client.post(
                    "/api/echo", json={"text": "hi"}, headers={"accept": accept}
                )
                self.assertEqual(response.status_code, 406)
                self.assertEqual(response.headers["content-type"], PROBLEM)

    def test_a_body_not_of_json_is_refused(self) -> None:
        response = self.client.post("/api/echo", data={"text": "hi"})
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.headers["content-type"], PROBLEM)

    def test_json_passes(self) -> None:
        for accept in ("application/json", "*/*", "text/html, application/*;q=0.5"):
            with self.subTest(accept=accept):
                response = self.client.post(
                    "/api/echo", json={"text": "hi"}, headers={"accept": accept}
                )
                self.assertEqual(response.json(), {"text": "hi"})

    def test_the_errors_are_problems(self) -> None:
        for method, path, status in (
            ("GET", "/api/nope", 404),
            ("GET", "/api/fail", 405),
            ("POST", "/api/fail", 409),
        ):
            with self.subTest(path=path):
                response = self.client.request(method, path, json={"text": "hi"})
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.headers["content-type"], PROBLEM)


class PagesTestCase(unittest.TestCase):
    @t.override
    def setUp(self) -> None:
        self.client = self.enterContext(TestClient(app))

    def test_a_form_posted_redirects(self) -> None:
        response = self.client.post(
            "/echo", data={"text": "hi <b>"}, follow_redirects=False
        )
        self.assertEqual(response.status_code, 303)
        page = self.client.get(response.headers["location"])
        self.assertEqual(page.headers["content-type"], HTML)
        self.assertIn("<output>hi &lt;b&gt;</output>", page.text)

    def test_the_errors_are_pages(self) -> None:
        for method, path, status, title in (
            ("GET", "/nope", 404, "Not Found"),
            ("GET", "/echo", 405, "Method Not Allowed"),
            ("POST", "/fail", 409, "The echo failed"),
        ):
            with self.subTest(path=path):
                response = self.client.request(method, path, data={"text": "<b>"})
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.headers["content-type"], HTML)
                self.assertIn(f"<h1>{title}</h1>", response.text)
        self.assertIn("&#x27;&lt;b&gt;&#x27;", response.text)  # the detail, escaped


class GuardsTestCase(unittest.TestCase):
    def test_accepts_json(self) -> None:
        for accept, expected in (
            (None, True),
            ("", True),
            ("*/*", True),
            ("application/*", True),
            ("application/problem+json", True),
            ("application/json; charset=utf-8", True),
            ("text/html, application/json;q=0.1", True),
            ("application/json;q=0, */*", True),  # a problem is JSON still
            ("application/json;q=0, application/problem+json;q=0", False),
            ("application/*;q=0", False),
            ("text/html", False),
            ("application/json;q=nope", False),
        ):
            with self.subTest(accept=accept):
                self.assertIs(accepts_json(accept), expected)

    def test_is_json(self) -> None:
        for content_type, expected in (
            ("application/json", True),
            ("Application/JSON; charset=utf-8", True),
            ("application/merge-patch+json", True),
            ("application/x-www-form-urlencoded", False),
            ("text/json", False),
            ("", False),
        ):
            with self.subTest(content_type=content_type):
                self.assertIs(is_json(content_type), expected)


class LinkingHtmlProblemRenderer(StarletteHtmlProblemRenderer):
    """A page of a problem of the application: a link home, of the request."""

    @t.override
    def _render_page(
        self, problem: StarletteProblem, connection: HTTPConnection
    ) -> str:
        home = connection.url_for("home")
        return f'<h1>{problem.status}</h1><a href="{home}">home</a>'


class LinkingPagesUnit(EchoPagesUnit):
    renderer = Slot(LinkingHtmlProblemRenderer)


class LinkingStarletteUnit(EchoStarletteUnit):
    pages = Slot(LinkingPagesUnit)


class LinkingProject(EchoProject):
    starlette = Slot(LinkingStarletteUnit)


class RendererTestCase(unittest.TestCase):
    def test_a_page_of_a_problem_takes_the_request(self) -> None:
        with TestClient(StarletteRunner(LinkingProject)) as client:
            response = client.get("/nope")
        self.assertEqual(response.status_code, 404)
        self.assertIn('<a href="http://testserver/">home</a>', response.text)


class SocketPageTestCase(unittest.TestCase):
    def test_the_page_opens_the_websocket_of_its_site(self) -> None:
        with TestClient(app) as client:
            response = client.get("/socket")
            self.assertEqual(response.headers["content-type"], HTML)
            self.assertIn("/ws/stream", response.text)
            self.assertIn('href="/socket"', client.get("/").text)
