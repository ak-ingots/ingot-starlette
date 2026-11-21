"""The floor of a failure: the same problem on Starlette alone."""

import typing as t

from ingots.perf import LoadClient, LoadGroup, PerfUnit
from ingots.puer import Slot
from project import BODY, DemoPerfProject, build_post, check_status


class RawFailer(LoadClient["PerfProject", "RawFailerGroup"]):
    @t.override
    async def asyncSetUp(self) -> None:
        server = await self.project.http.raw
        self.connection = await server.connect()
        self.request = build_post(server.get_host(), "/api/fail", BODY)

    @t.override
    async def run(self) -> None:
        async with self.measure("fail-echo"):
            check_status(await self.connection.send(self.request), 409)


class RawFailerGroup(LoadGroup[None]):
    clients = (RawFailer,)


class RawFailEchoPerf(PerfUnit[None]):
    group = RawFailerGroup


class PerfProject(DemoPerfProject):
    perf = Slot(RawFailEchoPerf)
