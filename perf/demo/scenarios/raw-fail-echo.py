"""The floor of a failure: the same problem on Starlette alone."""

import typing as t

from ingots.perf import LoadClient, LoadGroup, PerfUnit
from ingots.puer import Slot
from project import BODY, DemoPerfProject, check_status


class RawFailer(LoadClient["PerfProject", "RawFailerGroup"]):
    @t.override
    async def asyncSetUp(self) -> None:
        self.http = (await self.project.http.raw).client

    @t.override
    async def run(self) -> None:
        async with self.measure("fail-echo"):
            response = await self.http.post("/api/fail", json=BODY)
            check_status(response, 409)


class RawFailerGroup(LoadGroup[None]):
    clients = (RawFailer,)


class RawFailEchoPerf(PerfUnit[None]):
    group = RawFailerGroup


class PerfProject(DemoPerfProject):
    perf = Slot(RawFailEchoPerf)
