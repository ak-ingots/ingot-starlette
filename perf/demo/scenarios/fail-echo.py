"""A failure through the policy of ingot-starlette: its problem, 409."""

import typing as t

from ingots.perf import LoadClient, LoadGroup, PerfUnit
from ingots.puer import Slot
from project import BODY, DemoPerfProject, check_status


class Failer(LoadClient["PerfProject", "FailerGroup"]):
    @t.override
    async def asyncSetUp(self) -> None:
        self.http = (await self.project.http.default).client

    @t.override
    async def run(self) -> None:
        async with self.measure("fail-echo"):
            response = await self.http.post("/api/fail", json=BODY)
            check_status(response, 409)


class FailerGroup(LoadGroup[None]):
    clients = (Failer,)


class FailEchoPerf(PerfUnit[None]):
    group = FailerGroup


class PerfProject(DemoPerfProject):
    perf = Slot(FailEchoPerf)
