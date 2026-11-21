"""An echo through the endpoint of ingot-starlette, for the anonymous caller."""

import typing as t

from ingots.perf import LoadClient, LoadGroup, PerfUnit
from ingots.puer import Slot
from project import BODY, DemoPerfProject, check_status


class Sender(LoadClient["PerfProject", "SenderGroup"]):
    @t.override
    async def asyncSetUp(self) -> None:
        self.http = (await self.project.http.default).client

    @t.override
    async def run(self) -> None:
        async with self.measure("send-echo"):
            response = await self.http.post("/api/echo", json=BODY)
            check_status(response, 200)


class SenderGroup(LoadGroup[None]):
    clients = (Sender,)


class SendEchoPerf(PerfUnit[None]):
    group = SenderGroup


class PerfProject(DemoPerfProject):
    perf = Slot(SendEchoPerf)
