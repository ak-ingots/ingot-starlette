"""The floor of an echo: the same route on Starlette alone."""

import typing as t

from ingots.perf import LoadClient, LoadGroup, PerfUnit
from ingots.puer import Slot
from project import BODY, DemoPerfProject, check_status


class RawSender(LoadClient["PerfProject", "RawSenderGroup"]):
    @t.override
    async def asyncSetUp(self) -> None:
        self.http = (await self.project.http.raw).client

    @t.override
    async def run(self) -> None:
        async with self.measure("send-echo"):
            response = await self.http.post("/api/echo", json=BODY)
            check_status(response, 200)


class RawSenderGroup(LoadGroup[None]):
    clients = (RawSender,)


class RawSendEchoPerf(PerfUnit[None]):
    group = RawSenderGroup


class PerfProject(DemoPerfProject):
    perf = Slot(RawSendEchoPerf)
