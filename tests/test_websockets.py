"""The WebSockets of examples/demo: the subtree at /ws, a resource each."""

import asyncio
import typing as t
import unittest

from asgi import app
from project import EchoProject
from extensions.starlette import EchoStarletteUnit
from extensions.starlette.ws import EchoWebSocketsUnit
from ingots.puer import Factory, Slot
from starlette.testclient import TestClient, WebSocketDenialResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from ingot_starlette.runner import StarletteRunner
from ingot_starlette.starlette.websockets import (
    BaseStarletteWebSocketResource,
    StarletteWebSocketRoute,
)
from ingot_starlette.starlette.websockets.guards import is_origin_allowed

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class StreamTestCase(unittest.TestCase):
    def test_each_message_is_echoed(self) -> None:
        with TestClient(app) as client, client.websocket_connect("/ws/stream") as ws:
            for text in ("one", "two"):
                ws.send_json({"text": text})
                self.assertEqual(ws.receive_json(), {"text": text})

    def test_a_failure_closes_by_its_status(self) -> None:
        with TestClient(app) as client, client.websocket_connect("/ws/stream") as ws:
            ws.send_json({"text": "fail"})
            self.assertEqual(ws.receive_json()["problem"]["status"], 409)
            with self.assertRaises(WebSocketDisconnect) as caught:
                ws.receive_text()
        self.assertEqual(caught.exception.code, 4409)

    def test_a_message_not_json_closes_by_400(self) -> None:
        with TestClient(app) as client, client.websocket_connect("/ws/stream") as ws:
            ws.send_text("hi")
            self.assertEqual(ws.receive_json()["problem"]["status"], 400)
            with self.assertRaises(WebSocketDisconnect) as caught:
                ws.receive_text()
        self.assertEqual(caught.exception.code, 4400)


class ChatTestCase(unittest.TestCase):
    def test_unary_and_stream_on_one_connection(self) -> None:
        with TestClient(app) as client, client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"op": "ticks", "interval": 0.01})
            self.assertEqual(ws.receive_json(), {"tick": 1})
            ws.send_json({"op": "echo", "text": "hi"})
            received = [ws.receive_json() for _ in range(20)]
            self.assertIn({"echo": "hi"}, received)
            ws.send_json({"op": "stop"})

    def test_a_failure_is_a_message_the_connection_kept(self) -> None:
        with TestClient(app) as client, client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"op": "ticks", "count": 5, "interval": 0, "fail_at": 2})
            self.assertEqual(ws.receive_json(), {"tick": 1})
            self.assertEqual(ws.receive_json()["problem"]["status"], 409)
            ws.send_json({"op": "echo", "text": "still"})
            self.assertEqual(ws.receive_json(), {"echo": "still"})

    def test_the_stream_closes_with_the_connection(self) -> None:
        with TestClient(app) as client:
            with self.assertLogs("echo.operations", "INFO") as logs:
                with client.websocket_connect("/ws/chat") as ws:
                    ws.send_json({"op": "ticks", "interval": 0.01})
                    ws.receive_json()
        self.assertTrue(any("closed at" in line for line in logs.output))


class GuardsTestCase(unittest.TestCase):
    def test_a_request_of_http_is_refused_by_426(self) -> None:
        with TestClient(app) as client:
            response = client.get("/ws/stream")
        self.assertEqual(response.status_code, 426)
        self.assertEqual(response.headers["upgrade"], "websocket")
        self.assertEqual(response.headers["content-type"], "application/problem+json")

    def test_another_origin_is_refused(self) -> None:
        with TestClient(app) as client:
            with self.assertRaises(WebSocketDenialResponse) as caught:
                with client.websocket_connect(
                    "/ws/stream", headers={"origin": "https://evil.example.com"}
                ):
                    pass  # pragma: no cover
            self.assertEqual(caught.exception.status_code, 403)
            with client.websocket_connect(
                "/ws/stream", headers={"origin": "http://testserver"}
            ) as ws:
                ws.send_json({"text": "same site"})
                self.assertEqual(ws.receive_json(), {"text": "same site"})

    def test_an_origin_allowed(self) -> None:
        with TestClient(StarletteRunner(RefusingProject)) as client:
            with client.websocket_connect(
                "/ws/stream", headers={"origin": "https://app.example.com"}
            ) as ws:
                ws.send_json({"text": "hi"})
                self.assertEqual(ws.receive_json(), {"text": "hi"})

    def test_a_websocket_is_not_of_the_api(self) -> None:
        with TestClient(app) as client:
            with self.assertRaises(WebSocketDenialResponse) as caught:
                with client.websocket_connect("/api/echo"):
                    pass  # pragma: no cover
        self.assertEqual(caught.exception.status_code, 404)

    def test_is_origin_allowed(self) -> None:
        for origin, host, expected in (
            (None, "a.com", True),
            ("https://a.com", "a.com", True),
            ("https://a.com:8443", "a.com:8443", True),
            ("https://b.com", "a.com", False),
            ("https://ok.com", "a.com", True),
            ("https://a.com", None, False),
        ):
            with self.subTest(origin=origin, host=host):
                self.assertIs(
                    is_origin_allowed(origin, host, {"https://ok.com"}), expected
                )


class RefusedResource(BaseStarletteWebSocketResource):
    """Refused before the accept: its caller may not."""

    project: "RefusingProject"

    @t.override
    async def _open(self) -> None:
        await self.run_operation(self.project.echo.op_fail, "refused")

    @t.override
    async def _receive(self, message: t.Any) -> None:
        raise AssertionError("never: refused")  # pragma: no cover


class WaitingResource(BaseStarletteWebSocketResource):
    """Waits, cancelled by the test as a shutdown cancels it; opened slowly if told."""

    @t.override
    async def _open(self) -> None:
        if self.websocket.query_params.get("slow"):
            await asyncio.sleep(10)

    @t.override
    async def _receive(self, message: t.Any) -> None:
        await asyncio.sleep(10)


class RefusingWebSocketsUnit(EchoWebSocketsUnit):
    refused = Factory(RefusedResource)
    waiting = Factory(WaitingResource)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield from super()._iter_routes()
        yield StarletteWebSocketRoute("/refused", self.refused)
        yield StarletteWebSocketRoute("/waiting", self.waiting)

    @t.override
    def _iter_origins(self) -> "Iterator[str]":
        yield "https://app.example.com"


class RefusingStarletteUnit(EchoStarletteUnit):
    ws = Slot(RefusingWebSocketsUnit)


class RefusingProject(EchoProject):
    starlette = Slot(RefusingStarletteUnit)


class ResourceTestCase(unittest.TestCase):
    def test_a_failure_before_the_accept_refuses(self) -> None:
        with TestClient(StarletteRunner(RefusingProject)) as client:
            with self.assertRaises(WebSocketDenialResponse) as caught:
                with client.websocket_connect("/ws/refused"):
                    pass  # pragma: no cover
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.json()["status"], 409)


class ShutdownTestCase(unittest.IsolatedAsyncioTestCase):
    @t.override
    async def asyncSetUp(self) -> None:
        self.project = RefusingProject()
        await self.project._configure()
        self.addAsyncCleanup(self.project._do_shut_down)
        self.received: "asyncio.Queue[t.MutableMapping[str, t.Any]]" = asyncio.Queue()
        self.sent: "asyncio.Queue[t.MutableMapping[str, t.Any]]" = asyncio.Queue()

    def serve(self, query: bytes) -> "tuple[asyncio.Task[None], WaitingResource]":
        scope = {
            "type": "websocket",
            "path": "/ws/waiting",
            "headers": [],
            "query_string": query,
        }
        websocket = WebSocket(scope, self.received.get, self.sent.put)
        resource = self.project.starlette.ws.waiting()
        return asyncio.create_task(resource.serve(websocket)), resource

    async def test_a_cancel_closes_as_going_away(self) -> None:
        self.received.put_nowait({"type": "websocket.connect"})
        self.received.put_nowait({"type": "websocket.receive", "text": "{}"})
        task, resource = self.serve(b"")
        self.assertEqual((await self.sent.get())["type"], "websocket.accept")
        await asyncio.sleep(0.01)  # in _receive
        self.assertEqual(resource.caller.uid, "anonymous")
        self.assertEqual(resource.websocket.url.path, "/ws/waiting")
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        close = {"type": "websocket.close", "code": 1001, "reason": ""}
        self.assertEqual(await self.sent.get(), close)

    async def test_a_cancel_before_the_accept_closes_nothing(self) -> None:
        task, _ = self.serve(b"slow=1")
        await asyncio.sleep(0.01)  # in _open
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(self.sent.empty())
