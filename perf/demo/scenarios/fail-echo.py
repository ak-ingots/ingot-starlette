"""A failure through the policy of ingot-starlette: its problem, 409."""

import typing as t

from ingots.perf import LoadClient, LoadGroup, PerfUnit
from ingots.puer import Slot
from project import BODY, DemoPerfProject, build_post, check_status


class Failer(LoadClient["PerfProject", "FailerGroup"]):
    @t.override
    async def asyncSetUp(self) -> None:
        server = await self.project.http.default
        self.connection = await server.connect()
        self.request = build_post(server.get_host(), "/api/fail", BODY)

    @t.override
    async def run(self) -> None:
        async with self.measure("fail-echo"):
            check_status(await self.connection.send(self.request), 409)


class FailerGroup(LoadGroup[None]):
    clients = (Failer,)


class FailEchoPerf(PerfUnit[None]):
    group = FailerGroup


class PerfProject(DemoPerfProject):
    perf = Slot(FailEchoPerf)
