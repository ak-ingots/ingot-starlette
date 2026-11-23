"""
What the scenarios of the load of the demo share: the project of the
client with the configs of a run, ``PerfConfigs`` of ingots joined to its
own, and its servers of HTTP, components opening the connections of the
clients: ``default`` the application on ``DEMO_PORT``, ``bare`` the floor of
the stand, Starlette alone, on ``DEMO_BARE_PORT``.

The client of HTTP is of asyncio, as light as it gets, so that the server,
not the load, is what saturates: a connection kept alive for each client of
the load, its requests built once by h11, then sent as bytes, a response
read by its ``Content-Length``, its status checked, its body dropped.
"""

import abc
import asyncio
import json
import typing as t

import h11

from ingots.defaults import Project
from ingots.defaults.settings import SettingsUnit
from ingots.defaults.settings.configs import IntConfig, StrConfig
from ingots.perf import PerfConfigs
from ingots.puer import Component, Slot, Unit


class DemoPerfConfigs(PerfConfigs):
    DEMO_HOST = StrConfig("127.0.0.1")
    DEMO_PORT = IntConfig(8071)  # the application
    DEMO_BARE_PORT = IntConfig(8072)  # its floor, Starlette alone


class DemoPerfSettingsUnit(SettingsUnit):
    configs = Slot(DemoPerfConfigs)


class UnexpectedResponseError(Exception):
    """A response the scenario does not expect. Create it with a classmethod."""

    @classmethod
    def for_status(cls, status: int, expected: int) -> t.Self:
        return cls(f"the status {status}, not {expected}", status)

    @classmethod
    def for_head(cls, head: bytes) -> t.Self:
        return cls(f"no Content-Length in {head[:80]!r}", head)


class HttpConnection:
    """
    A connection of HTTP/1.1 kept alive, a request at a time: :meth:`send`
    writes the bytes of a request :func:`build_post` built and reads the
    response, giving its status.
    """

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._reader = reader
        self._writer = writer

    async def send(self, request: bytes) -> int:
        """Sends a request and reads its response: its status."""
        self._writer.write(request)
        head = await self._reader.readuntil(b"\r\n\r\n")
        status = int(head[9:12])  # HTTP/1.1 200 OK
        start = head.lower().find(b"\r\ncontent-length:")
        if start < 0:
            raise UnexpectedResponseError.for_head(head)
        end = head.index(b"\r\n", start + 2)
        await self._reader.readexactly(int(head[start + 17 : end]))
        return status

    async def close(self) -> None:
        self._writer.close()
        await self._writer.wait_closed()


class BaseDemoHttpServer(Component):
    """
    A server of the stand: it opens the connections of the clients of the
    load, by :meth:`connect`, and closes them at the shutdown.
    """

    SHUTDOWN_ORDER = 8

    project: "DemoPerfProject"

    _connections: list[HttpConnection]

    @t.override
    def __repr__(self) -> str:
        return f"<{type(self).__qualname__} {self.get_host()}:{self._get_port()}>"

    @t.final
    def get_host(self) -> str:
        """The host of the server, as a request names it."""
        return self.project.settings.configs.DEMO_HOST

    @t.final
    async def connect(self) -> HttpConnection:
        """A connection of a client of the load, kept alive."""
        reader, writer = await asyncio.open_connection(
            self.get_host(), self._get_port()
        )
        connection = HttpConnection(reader, writer)
        self._connections.append(connection)
        return connection

    @t.override
    async def _configure(self) -> None:
        self._connections = []

    @t.override
    async def _shut_down(self) -> None:
        connections, self._connections = self._connections, []
        await asyncio.gather(
            *(connection.close() for connection in connections), return_exceptions=True
        )

    @abc.abstractmethod
    def _get_port(self) -> int:
        raise NotImplementedError


class DefaultDemoHttpServer(BaseDemoHttpServer):
    @t.override
    def _get_port(self) -> int:
        return self.project.settings.configs.DEMO_PORT


class BareDemoHttpServer(BaseDemoHttpServer):
    @t.override
    def _get_port(self) -> int:
        return self.project.settings.configs.DEMO_BARE_PORT


class DemoHttpUnit(Unit):
    default = Slot(DefaultDemoHttpServer)
    bare = Slot(BareDemoHttpServer)


class DemoPerfProject(Project):
    """The project of a scenario, which adds its unit ``perf``."""

    env_configs_prefix = "PERF_TEST"
    settings = Slot(DemoPerfSettingsUnit)
    http = Slot(DemoHttpUnit)


def build_post(host: str, path: str, data: object) -> bytes:
    """
    The bytes of a request ``POST`` of a body of JSON, built once by h11, as
    a client of HTTP/1.1 sends them; a connection kept alive sends them
    again and again.
    """
    body = json.dumps(data).encode()
    headers = [
        ("Host", host),
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(body))),
    ]
    connection = h11.Connection(h11.CLIENT)
    return b"".join(
        connection.send(event) or b""
        for event in (
            h11.Request(method="POST", target=path, headers=headers),
            h11.Data(data=body),
            h11.EndOfMessage(),
        )
    )


def check_status(status: int, expected: int) -> None:
    """Raises :class:`UnexpectedResponseError` unless the status is ``expected``."""
    if status != expected:
        raise UnexpectedResponseError.for_status(status, expected)


# the text of every echo: its size is not under test
TEXT: t.Final = "hello"
BODY: t.Final = {"text": TEXT}
