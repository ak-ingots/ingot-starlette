"""The floor of an echo: the same route on Starlette alone."""

import typing as t

from ingots.perf import LoadClient, LoadGroup, PerfUnit
from ingots.puer import Slot
from load import BODY, DemoPerfProject, build_post, check_status


class BareSender(LoadClient["PerfProject", "BareSenderGroup"]):
    @t.override
    async def asyncSetUp(self) -> None:
        server = await self.project.http.bare
        self.connection = await server.connect()
        self.request = build_post(server.get_host(), "/api/echo", BODY)

    @t.override
    async def run(self) -> None:
        async with self.measure("send-echo"):
            check_status(await self.connection.send(self.request), 200)


class BareSenderGroup(LoadGroup[None]):
    clients = (BareSender,)


class BareSendEchoPerf(PerfUnit[None]):
    group = BareSenderGroup


class PerfProject(DemoPerfProject):
    perf = Slot(BareSendEchoPerf)
