"""The runner: the application of Starlette, the project inside."""

import asyncio
import unittest
from unittest import mock

import httpx
import uvicorn
from project import EchoProject
from ingots.defaults.cli import ProjectCliArgs
from ingots.puer import UserError
from starlette.exceptions import HTTPException
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Route, Router
from starlette.testclient import TestClient

from ingot_starlette.runner import StarletteRunner


class RunnerTestCase(unittest.TestCase):
    def test_no_lifespan_runs_no_project(self) -> None:
        client = TestClient(StarletteRunner(EchoProject))
        with self.assertRaisesRegex(RuntimeError, "no project is running"):
            client.get("/health/")

    def test_the_configs_reach_the_application(self) -> None:
        runner = StarletteRunner(
            EchoProject, ProjectCliArgs(configs=(("STARLETTE_IS_DEBUG", "on"),))
        )
        with TestClient(runner):
            self.assertTrue(runner.debug)
            self.assertIsInstance(runner.project, EchoProject)
        with self.assertRaises(RuntimeError):
            runner.project

    def test_a_failed_configuring_fails_the_startup(self) -> None:
        runner = StarletteRunner(EchoProject)
        error = UserError("no such file")
        with (
            mock.patch.object(EchoProject, "_configure", side_effect=error),
            self.assertLogs("ingot_starlette", "ERROR") as logs,
            self.assertRaises(UserError),
            TestClient(runner),
        ):
            pass  # pragma: no cover
        self.assertIsNone(logs.records[0].exc_info)

    def test_a_fault_of_configuring_is_logged_with_its_traceback(self) -> None:
        runner = StarletteRunner(EchoProject)
        with (
            mock.patch.object(EchoProject, "_configure", side_effect=ValueError("bad")),
            self.assertLogs("ingot_starlette", "ERROR") as logs,
            self.assertRaises(ValueError),
            TestClient(runner),
        ):
            pass  # pragma: no cover
        self.assertIn("ValueError: bad", logs.output[0])


class ServerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_uvicorn_serves_the_runner(self) -> None:
        config = uvicorn.Config(
            StarletteRunner(EchoProject),
            host="127.0.0.1",
            port=0,
            lifespan="on",
            log_level="warning",
        )
        server = uvicorn.Server(config)
        task = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.01)
        (socket,) = server.servers[0].sockets
        host, port = socket.getsockname()[:2]
        try:
            async with httpx.AsyncClient(base_url=f"http://{host}:{port}") as client:
                response = await client.post("/api/echo", json={"text": "hi"})
            self.assertEqual(response.json(), {"text": "hi"})
        finally:
            server.should_exit = True
            await task


async def homepage(request: Request) -> Response:
    return JSONResponse({"hello": "world"})


class StarletteApiTestCase(unittest.TestCase):
    """What the application is given as Starlette's stays beside the project's."""

    def test_the_routes_middleware_and_handlers_of_starlette_stay(self) -> None:
        runner = StarletteRunner(EchoProject)
        runner.add_route("/hello", homepage)
        runner.add_route("/teapot", teapot)
        runner.mount("/old", Router([Route("/", homepage)]))
        runner.add_middleware(GZipMiddleware, minimum_size=1)
        runner.add_exception_handler(404, not_found)
        runner.debug = True
        for _ in range(2):  # a lifespan anew builds on them, not on the last
            with TestClient(runner) as client:
                self.assertEqual(client.get("/hello").json(), {"hello": "world"})
                self.assertEqual(client.get("/old/").json(), {"hello": "world"})
                response = client.post("/api/echo", json={"text": "hi"})
                self.assertEqual(response.json(), {"text": "hi"})
                self.assertEqual(response.headers["content-encoding"], "gzip")
                # outside the subtrees, the handlers of Starlette; inside, theirs
                self.assertEqual(client.get("/teapot").text, "no page")
                response = client.get("/nope")
                self.assertEqual(response.status_code, 404)
                self.assertIn("<h1>Not Found</h1>", response.text)
                response = client.post("/api/fail", json={"text": "hi"})
                self.assertEqual(response.status_code, 409)  # a policy still
                self.assertTrue(runner.debug)
            # its routes, its mount, the three mounts of the project
            self.assertEqual(len(runner.routes), 2 + 1 + 3)


async def teapot(request: Request) -> Response:
    raise HTTPException(404)


async def not_found(request: Request, error: Exception) -> Response:
    return PlainTextResponse("no page", status_code=404)
