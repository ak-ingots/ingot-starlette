"""An echo through the endpoint of ingot-starlette, for the anonymous caller."""

import typing as t

from ingots.perf import LoadClient, LoadGroup, PerfUnit
from ingots.puer import Slot
from project import BODY, DemoPerfProject, build_post, check_status


class Sender(LoadClient["PerfProject", "SenderGroup"]):
    @t.override
    async def asyncSetUp(self) -> None:
        server = await self.project.http.default
        self.connection = await server.connect()
        self.request = build_post(server.get_host(), "/api/echo", BODY)

    @t.override
    async def run(self) -> None:
        async with self.measure("send-echo"):
            check_status(await self.connection.send(self.request), 200)


class SenderGroup(LoadGroup[None]):
    clients = (Sender,)


class SendEchoPerf(PerfUnit[None]):
    group = SenderGroup


class PerfProject(DemoPerfProject):
    perf = Slot(SendEchoPerf)
