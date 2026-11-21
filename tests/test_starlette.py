"""The Starlette unit and its errors, of the addon alone."""

import asyncio
import typing as t
import unittest
from unittest import mock

from ingots.puer import Slot
from starlette.requests import Request
from starlette.routing import Mount
from starlette.testclient import TestClient

from ingot_starlette import StarletteProject
from ingot_starlette.runner import StarletteRunner
from ingot_starlette.starlette import StarletteEndpoint, StarletteUnit
from ingot_starlette.starlette.errors import (
    BaseStaticStarletteErrorPolicy,
    StarletteErrorsUnit,
    StarletteProblem,
    encode_problem,
)

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute


class UnitTestCase(unittest.TestCase):
    def test_the_unit_of_the_addon_routes_nothing(self) -> None:
        with TestClient(StarletteRunner(StarletteProject)) as client:
            response = client.get("/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"], "application/problem+json")

    def test_an_endpoint_of_the_addon_routes_nothing(self) -> None:
        with TestClient(StarletteRunner(EndpointProject)) as client:
            self.assertEqual(client.get("/").status_code, 404)


class EndpointStarletteUnit(StarletteUnit):
    endpoint = Slot(StarletteEndpoint)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield Mount("/endpoint", routes=self.endpoint.get_routes())


class EndpointProject(StarletteProject):
    starlette = Slot(EndpointStarletteUnit)


class ErrorsTestCase(unittest.TestCase):
    def test_an_exception_has_one_policy(self) -> None:
        class FirstPolicy(BaseStaticStarletteErrorPolicy):
            EXCEPTION = KeyError
            STATUS = 404

        class SecondPolicy(BaseStaticStarletteErrorPolicy):
            EXCEPTION = KeyError
            STATUS = 410

        with self.assertRaisesRegex(TypeError, "KeyError has both first and second"):

            class AppStarletteErrorsUnit(StarletteErrorsUnit):
                first = Slot(FirstPolicy)
                second = Slot(SecondPolicy)

    def test_a_failure_in_the_band_finds_its_policy_by_the_mro(self) -> None:
        runner = StarletteRunner(StarletteProject)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/stream",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
            "root_path": "",
        }
        with TestClient(runner), self.assertLogs("ingot_starlette", "ERROR"):
            errors = runner.project.starlette.errors
            problem = errors.encode(KeyError("lost"), Request(scope))
        self.assertEqual(problem.status, 500)  # of Exception, its base

    def test_a_problem_of_no_title_nor_detail(self) -> None:
        problem = StarletteProblem(status=418, extensions={"teapot": True})
        self.assertEqual(
            encode_problem(problem),
            {"type": "about:blank", "status": 418, "teapot": True},
        )


class LifespanTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_a_failed_shutdown_is_logged(self) -> None:
        runner = StarletteRunner(StarletteProject)
        to_app: "asyncio.Queue[dict[str, t.Any]]" = asyncio.Queue()
        from_app: "asyncio.Queue[t.MutableMapping[str, t.Any]]" = asyncio.Queue()
        lifespan = asyncio.ensure_future(
            runner({"type": "lifespan"}, to_app.get, from_app.put)
        )
        for message in ("lifespan.startup", "lifespan.unknown"):
            await to_app.put({"type": message})
        self.assertEqual(await from_app.get(), {"type": "lifespan.startup.complete"})
        with (
            mock.patch.object(
                StarletteProject, "_do_shut_down", side_effect=RuntimeError("stuck")
            ),
            self.assertLogs("ingot_starlette", "ERROR") as logs,
        ):
            await to_app.put({"type": "lifespan.shutdown"})
            self.assertEqual(
                await from_app.get(), {"type": "lifespan.shutdown.complete"}
            )
            await lifespan
        self.assertIn("shutting down failed", logs.output[0])
