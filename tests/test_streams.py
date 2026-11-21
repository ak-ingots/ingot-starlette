"""The streams of examples/demo: NDJSON over HTTP, a WebSocket."""

import json
import typing as t
import unittest

from demo.asgi import app
from demo.project import EchoProject
from demo.starlette import EchoStarletteUnit
from ingots.puer import Slot
from starlette.routing import WebSocketRoute
from starlette.testclient import TestClient, WebSocketDenialResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from ingot_starlette.runner import StarletteRunner

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class HttpStreamTestCase(unittest.TestCase):
    @t.override
    def setUp(self) -> None:
        self.client = self.enterContext(TestClient(app))

    def get_lines(self, **params: object) -> tuple[int, list[t.Any]]:
        response = self.client.get("/api/ticks", params={"interval": 0, **params})
        return response.status_code, [
            json.loads(line) for line in response.text.splitlines()
        ]

    def test_the_items_are_lines(self) -> None:
        self.assertEqual(
            self.get_lines(count=3), (200, [{"tick": 1}, {"tick": 2}, {"tick": 3}])
        )

    def test_a_failure_after_the_status_is_the_last_line(self) -> None:
        status, lines = self.get_lines(count=5, fail_at=3)
        self.assertEqual(status, 200)
        self.assertEqual(lines[:2], [{"tick": 1}, {"tick": 2}])
        self.assertEqual(lines[2]["problem"]["status"], 409)
        self.assertEqual(len(lines), 3)

    def test_a_failure_before_the_first_item_is_the_response(self) -> None:
        response = self.client.get("/api/ticks", params={"interval": 0, "fail_at": 1})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.headers["content-type"], "application/problem+json")

    def test_a_stream_of_no_item(self) -> None:
        self.assertEqual(self.get_lines(count=-1), (200, []))


class WebSocketTestCase(unittest.TestCase):
    def test_each_text_is_echoed(self) -> None:
        with TestClient(app) as client, client.websocket_connect("/api/stream") as ws:
            for text in ("one", "two"):
                ws.send_text(text)
                self.assertEqual(ws.receive_text(), text)

    def test_a_failure_closes_by_its_status(self) -> None:
        with TestClient(app) as client, client.websocket_connect("/api/stream") as ws:
            ws.send_text("fail")
            self.assertEqual(ws.receive_json()["problem"]["status"], 409)
            with self.assertRaises(WebSocketDisconnect) as caught:
                ws.receive_text()
        self.assertEqual(caught.exception.code, 4409)

    def test_a_failure_before_the_accept_refuses(self) -> None:
        with TestClient(StarletteRunner(RefusingProject)) as client:
            with self.assertRaises(WebSocketDenialResponse) as caught:
                with client.websocket_connect("/refused"):
                    pass  # pragma: no cover
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.json()["status"], 409)


class RefusingStarletteUnit(EchoStarletteUnit):
    project: "RefusingProject"

    async def refuse(self, websocket: WebSocket) -> None:
        await self.run_operation(self.project.echo.op_fail, "refused", websocket)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield from super()._iter_routes()
        yield WebSocketRoute("/refused", self.refuse)


class RefusingProject(EchoProject):
    starlette = Slot(RefusingStarletteUnit)
